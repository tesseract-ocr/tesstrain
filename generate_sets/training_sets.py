# -*- coding: utf-8 -*-
"""Generate TrainingSets Sets"""

import abc
import os
from pathlib import (
    Path
)
from functools import reduce
import sys

import exifread
import lxml.etree as etree
import numpy as np

from cv2 import cv2
from PIL import (
    Image
)
from shapely.geometry import (
    Polygon
)


XML_NS = {
    'alto': 'http://www.loc.gov/standards/alto/ns-v3#',
    'page2013': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15',
    'page2019': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15'}

# default values
DEFAULT_MIN_CHARS = 1
DEFAULT_OUTDIR_PREFIX = 'training_data_'
DEFAULT_USE_SUMMARY = False
DEFAULT_USE_REORDER = False
DEFAULT_DPI = 300
SUMMARY_SUFFIX = '_summary.gt.txt'


class TextLine(abc.ABC):
    """
    TextLine from structured OCR-Data
    """

    def __init__(self, element, namespace, reorder=False):
        self.element = element
        self.namespace = namespace
        self.element_id = None
        self.valid = True
        self.set_id()
        self.text_words = []
        self.set_text()
        if self.valid:
            self.reorder = reorder
            self.box = self.to_box(self.element)

    @abc.abstractmethod
    def set_id(self):
        """Determine identifier"""

    @abc.abstractmethod
    def set_text(self):
        """Determine list of word tokens"""

    @abc.abstractmethod
    def to_box(self, element):
        """Return bounding box of TexLine shape"""

    def get_textline_content(self) -> str:
        """
        Set TextLine contents from it's included word tokens
        reorder order of tokens if required
        """

        aggregat = ' '.join(self.text_words)
        if self.reorder:
            return reduce(lambda c, p: p + ' ' + c, self.text_words)
        return aggregat

    def __repr__(self):
        return '{}:{}'.format(self.__class__.__name__, self.element_id)


class ALTOLine(TextLine):
    """Extract TextLine Information from ALTO Data"""

    def __init__(self, element, namespace, sanitize=True):
        super().__init__(element, namespace)
        if sanitize:
            self.sanitize_box()

    def set_id(self):
        self.element_id = self.element.attrib['ID']

    def set_text(self):
        strings = self.element.findall(f'{self.namespace}:String', XML_NS)
        self.text_words = [e.attrib['CONTENT'] for e in strings]

    def to_box(self, element):
        x_1 = int(element.attrib['HPOS'])
        y_1 = int(element.attrib['VPOS'])
        y_2 = y_1 + int(element.attrib['HEIGHT'])
        x_2 = x_1 + int(element.attrib['WIDTH'])
        return (x_1, y_1, x_2, y_2)

    def get_next_element_height(self, element):
        y_start = int(element.attrib['VPOS'])
        y_height = int(element.attrib['HEIGHT'])
        return y_start + y_height

    def sanitize_box(self):
        line_tokens = self.element.findall(f"{self.namespace}String", XML_NS)
        boxes = [self.to_box(s) for s in line_tokens]
        word_heights = [(y2 - y1) for _, y1, _, y2 in boxes]
        heights_std = np.std(word_heights)
        i = 1
        max_i = 4
        while heights_std > 10 and i <= max_i:
            outlier_height_index = np.argmax(word_heights)
            word_heights.pop(outlier_height_index)
            next_greatest_y2 = self.text_words[np.argmax(word_heights)]
            self.y_2 = self.get_next_element_height(next_greatest_y2)
            heights_std = np.std(word_heights)
            i += 1


class PageLine(TextLine):
    """Extract TextLine Information from PAGE Data"""

    def set_id(self):
        self.element_id = self.element.attrib['id']

    def set_text(self):
        """
        * set words as preferred text source, otherwise use text line
        * drop rtl-mark if contained
        * print lines without coords
        """

        texts = []
        text_els = self.element.findall(f'{self.namespace}:Word', XML_NS)
        for t in text_els:
            top_left = PageLine._pick_top_left(t, self.namespace)
            if not top_left:
                elem_id = t.attrib['id']
                print("[ERROR  ] skip '{}': invalid coords!".format(
                    elem_id), file=sys.stderr)
                self.valid = False
                return
            texts.append(t)

        # if no words assume t least text lines exist
        if not text_els:
            top_left = PageLine._pick_top_left(self.element, self.namespace)
            if not top_left:
                elem_id = self.element.attrib['id']
                print("[ERROR  ] skip '{}': invalid coords!".format(
                    elem_id), file=sys.stderr)
                self.valid = False
                return
            texts.append(self.element)

        sorted_els = sorted(
            texts,
            key=lambda w: int(PageLine._pick_top_left(w, self.namespace)))
        unicodes = [
            w.find(
                f'.//{self.namespace}:Unicode',
                XML_NS) for w in sorted_els]
        self.text_words = [u.text.strip() for u in unicodes]

        # elimiate read order mark
        for i, strip in enumerate(self.text_words):
            strip = self.text_words[i]
            if '\u200f' in strip:
                self.text_words[i] = strip.replace('\u200f', '')
        # enrich read order mark with latin digits
        for i, strip in enumerate(self.text_words):
            strip = self.text_words[i]
            if 'X' in strip or 'I' in strip or 'V' in strip:
                self.text_words[i] = '\u200f' + strip

    @staticmethod
    def _pick_top_left(elem, namespace):
        coords = elem.find(f'{namespace}:Coords', XML_NS)
        points = coords.attrib['points'].split()
        if len(points) > 0:
            return points[0].split(',')[0]

    def to_box(self, element):
        """
        Coordinate data from current OCR-D-Workflows might contain
        lots of points, therefore additional calculations required
        """

        p_attr = element.find(
            f'{self.namespace}:Coords',
            XML_NS).attrib['points']
        numbers = [int(n) for pair in p_attr.split() for n in pair.split(',')]

        # group clustering idiom
        points = list(zip(*[iter(numbers)] * 2))

        shape = Polygon(points)
        box = [int(n) for n in shape.bounds]
        return box


def text_line_factory(xml_data, min_len, reorder):
    """Create text_lines from given structured data"""

    text_lines = []
    ns_prefix = _determine_namespace(xml_data)
    if 'alto' in ns_prefix:
        all_lines = xml_data.findall(f'.//{ns_prefix}:TextLine', XML_NS)
        all_lines_len = [l for l in all_lines if len(' '.join(
            [s.attrib['CONTENT'] for s in l.findall(f'{ns_prefix}:String', XML_NS)])) >= min_len]
        text_lines = [ALTOLine(line, ns_prefix) for line in all_lines_len]
    elif ns_prefix in ('page2013', 'page2019'):
        all_lines = xml_data.findall(f'.//{ns_prefix}:TextLine', XML_NS)
        matchings = [
            l for l in all_lines if len(
                l.find(
                    f'{ns_prefix}:TextEquiv/{ns_prefix}:Unicode',
                    XML_NS).text.strip()) >= min_len]
        text_lines = [PageLine(line, ns_prefix, reorder) for line in matchings]

    # deliver only valid lines
    return [t for t in text_lines if t.valid]


def resolve_image_path(path_xml_data):
    """
    In Context of OCR-D-Workspace use information from PAGE
    to retrive matching image path
    """
    xml_data = etree.parse(path_xml_data).getroot()
    ns_prefix = _determine_namespace(xml_data)
    if ns_prefix in ('page2013', 'page2019'):
        img_file = xml_data.find(
            f'.//{ns_prefix}:Page', XML_NS).attrib['imageFilename']
        if img_file:
            workspace_dir = Path(path_xml_data).parent.parent
            img_path = os.path.join(workspace_dir, img_file)
            if not os.path.exists(img_path):
                raise RuntimeError(
                    f"can't handle invalid image_path : '{img_path}'")
            return img_path
    return None


def _determine_namespace(xml_data):
    root_tag = xml_data.xpath('namespace-uri(.)')
    return [k for (k, v) in XML_NS.items() if v == root_tag][0]


class TrainingSets:
    """
    Set of textlines and corresponding image parts created from given
    source if text_len > min
    """

    def __init__(self, path_xml_data, path_image_data):
        self.xdpi = None
        self.ydpi = None
        self.path_out = None
        (self.set_label, _) = os.path.splitext(os.path.basename(path_xml_data))
        self.xml_data = etree.parse(path_xml_data).getroot()
        self.path_image_data = path_image_data
        if not self.path_image_data:
            self._resolve_image_path(path_xml_data)
        self.image_data = TrainingSets._load_image(self.path_image_data)
        self._read_dpi()

    def _resolve_image_path(self, path_xml_data):
        self.path_image_data = resolve_image_path(path_xml_data)

    @staticmethod
    def _load_image(path_image_data):
        return cv2.imread(path_image_data, cv2.IMREAD_GRAYSCALE)

    def write_data(self, training_data: TextLine,
                   image_handle, path_out, prefix):
        """Serialize training data pairs"""

        if not path_out:
            path_out = prefix + self.set_label
        self.path_out = path_out
        os.makedirs(path_out, exist_ok=True)

        content = training_data.get_textline_content()
        if content:
            file_name = self.set_label + '_' + training_data.element_id + '.gt.txt'
            file_path = os.path.join(path_out, file_name)
            with open(file_path, 'w', encoding="utf8") as fhdl:
                fhdl.write(content)

            img_frame = TrainingSets._extract_frame(
                image_handle, training_data)
            file_name = self.set_label + '_' + training_data.element_id + '.tif'
            file_path = os.path.join(path_out, file_name)

            if img_frame.any():
                params = self._calculate_tiff_param()
                if params:
                    cv2.imwrite(file_path, img_frame, params)
                else:
                    cv2.imwrite(file_path, img_frame)

    def write_all(self, training_datas):
        """Serialize training data pairs"""

        contents = [d.get_textline_content() + '\n' for d in training_datas]
        file_name = self.set_label + SUMMARY_SUFFIX
        file_path = os.path.join(self.path_out, file_name)
        with open(file_path, 'w', encoding="utf8") as fhdl:
            fhdl.writelines(contents)

    @staticmethod
    def _extract_frame(image_handle, training_data):
        start_vpos = training_data.box[1]
        end_vpos = training_data.box[3]
        start_hpos = training_data.box[0]
        end_hpos = training_data.box[2]
        return image_handle[start_vpos:end_vpos, start_hpos:end_hpos]

    def _calculate_tiff_param(self):
        """
        Value '2' means 'inches':
        cf. https://www.loc.gov/preservation/digital/formats/content/tiff_tags.shtml
        """

        if self.xdpi and self.ydpi:
            return [cv2.IMWRITE_TIFF_RESUNIT, 2, cv2.IMWRITE_TIFF_XDPI, self.xdpi,
                    cv2.IMWRITE_TIFF_YDPI, self.ydpi]
        return []

    def _read_dpi(self):
        if str(self.path_image_data).endswith(".tif"):
            (self.xdpi, self.ydpi) = TrainingSets.read_dpi_from_tif(
                self.path_image_data)
        elif str(self.path_image_data).endswith(".jpg"):
            (self.xdpi, self.ydpi) = TrainingSets.read_dpi_from_jpg(
                self.path_image_data)

    @staticmethod
    def read_dpi_from_tif(path_image_data):
        """Determine DPI of TIF-Image EXIF-Data"""

        with open(path_image_data, 'rb') as fhdl:
            tags = exifread.process_file(fhdl)
            if tags:
                xdpi = None
                ydpi = None
                if 'Image XResolution' in tags:
                    xdpi = tags['Image XResolution'].values[0].num
                if 'Image YResolution' in tags:
                    ydpi = tags['Image YResolution'].values[0].num
                if xdpi and ydpi:
                    return (xdpi, xdpi)
        return (DEFAULT_DPI, DEFAULT_DPI)

    @staticmethod
    def read_dpi_from_jpg(path_image_data):
        """Determine DPI from JPG metadata"""

        image_file = Image.open(path_image_data)
        if 'dpi' in image_file.info:
            x_dpi, y_dpi = image_file.info['dpi']
            return (x_dpi, y_dpi)

        return (DEFAULT_DPI, DEFAULT_DPI)

    def create(self, folder_out=None,
               min_chars=DEFAULT_MIN_CHARS, prefix=DEFAULT_OUTDIR_PREFIX, summary=False, reorder=False):
        """
        Put training data sets which textlines consist of at least min_chars as
        text-image part pairs starting with prefix into folder_out
        """

        training_datas = text_line_factory(
            self.xml_data, min_len=min_chars, reorder=reorder)

        for training_data in training_datas:
            self.write_data(
                training_data,
                self.image_data,
                path_out=folder_out,
                prefix=prefix)

        if summary:
            self.write_all(training_datas)

        return training_datas
