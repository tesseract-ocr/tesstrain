# -*- coding: utf-8 -*-
"""OCR create pairs"""

import abc
import os

import exifread
import lxml.etree as etree
import numpy as np
from cv2 import cv2


XML_NS = {
    "alto": "http://www.loc.gov/standards/alto/ns-v3#",
    "page2013": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"}


class TrainingTextline(abc.ABC):
    """
    Wrapper for Extraction of Image-Segment + Textline Pairs from ALTO-Data
    """

    def __init__(self, element):
        self.element_id = None
        self._set_id(element)
        self.text_words = []
        self._set_text_words(element)
        self.textline_content = None
        self._set_texline_content()
        (self.x_1, self.y_1, self.x_2, self.y_2) = self.as_box(element)
        self._inspect_content()

    def _set_id(self, element):
        pass

    def _set_text_words(self, element):
        pass

    def _set_texline_content(self):
        pass

    @abc.abstractmethod
    def as_box(self, element):
        """Return shape points as bounding vox"""

    @abc.abstractmethod
    def get_next_element_height(self, element):
        """In case of sanitizing, get height of next element, i.e. word"""

    @abc.abstractmethod
    def must_sanitize(self):
        """Whether to start textline height correction"""

    def _inspect_content(self):
        if self.must_sanitize():
            word_heights = [
                (y2 -
                 y1) for (
                    _,
                    y1,
                    _,
                    y2) in (
                    self.as_box(s) for s in self.text_words)]
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

    def __repr__(self):
        return '{}:{}'.format(self.__class__.__name__, self.element_id)


class TrainingTextlineALTO(TrainingTextline):
    """Extract Textline Information from ALTO Data"""

    def _set_id(self, element):
        self.element_id = element.attrib['ID']

    def _set_text_words(self, element):
        self.text_words = element.findall('alto:String', XML_NS)

    def _set_texline_content(self):
        if self.text_words:
            self.textline_content = ' '.join(
                [s.attrib['CONTENT'] for s in self.text_words])

    def as_box(self, element):
        x_1 = int(element.attrib['HPOS'])
        y_1 = int(element.attrib['VPOS'])
        y_2 = y_1 + int(element.attrib['HEIGHT'])
        x_2 = x_1 + int(element.attrib['WIDTH'])
        return (x_1, y_1, x_2, y_2)

    def get_next_element_height(self, element):
        y_start = int(element.attrib['VPOS'])
        y_height = int(element.attrib['HEIGHT'])
        return y_start + y_height

    def must_sanitize(self):
        return True


class TrainingTextlinePage2013(TrainingTextline):
    """Extract Textline Information from PAGE 2013 Data"""

    def _set_id(self, element):
        self.element_id = element.attrib['id']

    def _set_text_words(self, element):
        self.text_words = element.findall(
            'page2013:TextEquiv/page2013:Unicode', XML_NS)

    def _set_texline_content(self):
        if self.text_words:
            self.textline_content = ' '.join([w.text for w in self.text_words])

    def as_box(self, element):
        (top_left, _, bottom_right, _) = element.find(
            'page2013:Coords', XML_NS).attrib['points'].split()
        x_1 = int(top_left.split(',')[0])
        y_1 = int(top_left.split(',')[1])
        x_2 = int(bottom_right.split(',')[0])
        y_2 = int(bottom_right.split(',')[1])
        return (x_1, y_1, x_2, y_2)

    def get_next_element_height(self, element):
        y_start = int(element.attrib['VPOS'])
        y_height = int(element.attrib['HEIGHT'])
        return y_start + y_height

    def must_sanitize(self):
        return False


def text_data_factory(path_xml_data, min_len):
    """Create text_line list from given xml data"""

    text_lines = []
    root = etree.parse(path_xml_data).getroot()
    root_tag = root.xpath('namespace-uri(.)')
    ns_prefix = [k for (k, v) in XML_NS.items() if v == root_tag][0]
    if 'alto' in ns_prefix:
        all_lines = root.findall(f'.//{ns_prefix}:TextLine', XML_NS)
        all_lines_len = [l for l in all_lines if len(' '.join(
            [s.attrib['CONTENT'] for s in l.findall(f'{ns_prefix}:String', XML_NS)])) >= min_len]
        text_lines = [TrainingTextlineALTO(line) for line in all_lines_len]
    elif ns_prefix == 'page2013':
        all_lines = root.iterfind(f'.//{ns_prefix}:TextLine', XML_NS)
        matchings = [
            l for l in all_lines if len(
                l.find(
                    'page2013:TextEquiv/page2013:Unicode',
                    XML_NS).text) >= min_len]
        text_lines = [TrainingTextlinePage2013(line) for line in matchings]

    return text_lines


class TrainingData:
    """
    Set of textlines and corresponding image parts created from given
    source if text_len > min
    """

    def __init__(self, path_xml_data, path_image_data):
        self.xdpi = None
        self.ydpi = None
        self.path_xml_data = path_xml_data
        (self.set_label, _) = os.path.splitext(os.path.basename(path_xml_data))

        self.path_image_data = path_image_data
        self.image_data = self._load_image(path_image_data)
        self._read_dpi()

    def _load_image(self, path_image_data):
        return cv2.imread(path_image_data, cv2.IMREAD_GRAYSCALE)

    def write_data(self, training_data: TrainingTextline,
                   image_handle, path_out, prefix):
        """Serialize training data pairs"""

        set_name = self.set_label
        if not path_out:
            path_out = prefix + set_name
        os.makedirs(path_out, exist_ok=True)

        content = training_data.textline_content
        if content:
            file_name = set_name + '_' + training_data.element_id + '.gt.txt'
            file_path = os.path.join(path_out, file_name)
            with open(file_path, 'w', encoding="utf8") as fhdl:
                fhdl.write(content)

            img_frame = TrainingData._extract_frame(
                image_handle, training_data)
            file_name = set_name + '_' + training_data.element_id + '.tif'
            file_path = os.path.join(path_out, file_name)

            if img_frame.any():
                params = self._calculate_tiff_param()
                if params:
                    cv2.imwrite(file_path, img_frame, params)
                else:
                    cv2.imwrite(file_path, img_frame)

    @staticmethod
    def _extract_frame(image_handle, training_data):
        start_vpos = training_data.y_1
        end_vpos = training_data.y_2
        start_hpos = training_data.x_1
        end_hpos = training_data.x_2
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
            (self.xdpi, self.ydpi) = TrainingData.read_dpi_from_tif(
                self.path_image_data)
        elif str(self.path_image_data).endswith(".jpg"):
            pass

    @staticmethod
    def read_dpi_from_tif(path_image_data):
        """Determine DPI of TIF-Image"""

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
        return None

    def create(self, folder_out=None,
               min_chars=16, prefix='training_data_'):
        """
        Put training data sets which textlines consist of at least min_chars as
        text-image part pairs starting with prefix into folder_out
        """

        training_datas = text_data_factory(
            self.path_xml_data, min_len=min_chars)

        for training_data in training_datas:
            self.write_data(
                training_data,
                self.image_data,
                path_out=folder_out,
                prefix=prefix)

        return training_datas
