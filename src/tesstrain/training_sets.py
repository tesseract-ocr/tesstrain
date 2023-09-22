# -*- coding: utf-8 -*-
"""Generate Training Sets from images data
and corresponding ALTO or PAGE files
"""

import abc
import math
import os
import sys

from functools import (
	reduce
)
from pathlib import (
    Path
)
from typing import (
    List
)

import exifread
import lxml.etree as etree
import numpy as np

from cv2 import (
    BORDER_CONSTANT,
    CHAIN_APPROX_SIMPLE,
    IMREAD_GRAYSCALE,
    IMWRITE_TIFF_RESUNIT,
    IMWRITE_TIFF_XDPI,
    IMWRITE_TIFF_YDPI,
    INTER_LINEAR,
    LINE_AA,
    RETR_TREE,
    THRESH_BINARY,
    THRESH_OTSU,
    boundingRect,
    copyMakeBorder,
    fillConvexPoly,
    fillPoly,
    filter2D,
    findContours,
    getRotationMatrix2D,
    imread,
    imwrite,
    minAreaRect,
    moments,
    resize,
    threshold,
    warpAffine,
    Canny,
    GaussianBlur,
    HoughLinesP,
)
from PIL import (
    Image
)


XML_NS = {
    'alto3': 'http://www.loc.gov/standards/alto/ns-v3#',
    'alto4': 'http://www.loc.gov/standards/alto/ns-v4#',
    'page2013': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15',
    'page2019': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15'}

# default values
DEFAULT_MIN_CHARS = 1
DEFAULT_OUTDIR_PREFIX = 'training_data_'
DEFAULT_USE_SUMMARY = False
DEFAULT_USE_REORDER = False
DEFAULT_DPI = 300
DEFAULT_INTRUSION_RATIO = 0.1  # top 1/10 and bottom 1/10
DEFAULT_ROTATION_THRESH = 0.1
DEFAULT_BINARIZE = False
DEFAULT_SANITIZE = True
DEFAULT_PADDING = 0
SUFFIX_SUMMARY = '_summary.gt.txt'
SUFFIX_GT_TXT_='.gt.txt'
SUFFIX_GT_IMG_TIF = '.tif'

# clear unwanted marks for single wordlike tokens
CLEAR_MARKS = [
    '\u200f',  # 'RIGHT-TO-LEFT-MARK'
    '\u200e',  # 'LEFT-TO-RIGHT-MARK'
    '\ufeff',  # 'ZERO WIDTH NO-BREAK SPACE', the char formerly known as 'BOM'
    '\u200c',  # 'ZERO WIDTH NON-JOINER
    '\u202c'   # 'POP DIRECTIONAL FORMATTING
]

class ExtractPairException(Exception):
    """Mark State Failure to create
    valid imagedata - text line pair
    """

class TextLine(abc.ABC):
    """
    TextLine from structured OCR-Data
    """

    def __init__(self, element, namespace):
        self.element = element
        self.namespace = namespace
        self.element_id = None
        self.valid = True
        self.text_words = []
        self.reorder = None
        self.vertical = False

    @abc.abstractmethod
    def set_id(self):
        """Determine identifier"""

    @abc.abstractmethod
    def set_text(self):
        """Determine list of word tokens"""

    def get_shape(self, _):
        """
        Return TextLine shape
        Optional(PAGE): Box filled with median color value
        or the_gray tone to fit rectangular shape
        """

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
        return f'{self.__class__.__name__}[{self.element_id}]:{self.get_textline_content()}'


class ALTOLine(TextLine):
    """Extract TextLine Information from ALTO Data"""

    def __init__(self, element, namespace):
        super().__init__(element, namespace)
        self.set_id()
        self.set_text()
        if self.valid:
            self.shape = self.get_shape(self.element)

    def set_id(self):
        self.element_id = self.element.attrib['ID']

    def set_text(self):
        strings = self.element.findall(f'{self.namespace}:String', XML_NS)
        self.text_words = [e.attrib['CONTENT'] for e in strings]

    def get_shape(self, element):
        x_1 = int(element.attrib['HPOS'])
        y_1 = int(element.attrib['VPOS'])
        y_2 = y_1 + int(element.attrib['HEIGHT'])
        x_2 = x_1 + int(element.attrib['WIDTH'])
        return [(x_1, y_1), (x_2, y_1), (x_2, y_2), (x_1, y_2)]

    def get_next_element_height(self, element):
        y_start = int(element.attrib['VPOS'])
        y_height = int(element.attrib['HEIGHT'])
        return y_start + y_height


class PageLine(TextLine):
    """Extract TextLine Information from PAGE Data"""

    def __init__(self, element, namespace, reorder):
        super().__init__(element, namespace)
        self.set_id()
        self.set_text()
        if self.valid:
            self.reorder = reorder
            self.shape = self.get_shape(self.element)

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
            top_left = to_center_coords(t, self.namespace, self.vertical)
            if not top_left:
                elem_id = t.attrib['id']
                msg = f"Invalid Coords of Word '{elem_id}' in '{self.element_id}'!"
                raise RuntimeError(msg)
            texts.append(t)

        # if no Word assume at least TextLine exists
        if not text_els:
            top_left = to_center_coords(self.element, self.namespace, self.vertical)
            if not top_left:
                elem_id = self.element.attrib['id']
                print(f"[ERROR  ] skip '{elem_id}': invalid coords!", file=sys.stderr)
                self.valid = False
                return
            texts.append(self.element)

        sorted_els = sorted(
            texts,
            key=lambda w: int(to_center_coords(w, self.namespace, self.vertical)))
        unicodes = [
            w.find(
                f'.//{self.namespace}:Unicode',
                XML_NS) for w in sorted_els]
        self.text_words = [u.text.strip() for u in unicodes if u.text]

        # elimiate read order mark
        for i, strip in enumerate(self.text_words):
            strip = self.text_words[i]
            for mark in CLEAR_MARKS:
                if mark in strip:
                    self.text_words[i] = strip.replace(mark, '')


    def get_shape(self, element):
        """
        Coordinate data from current OCR-D-Workflows can contain
        lots of points, therefore additional calculations are required
        """

        p_attr = element.find(
            f'{self.namespace}:Coords',
            XML_NS).attrib['points']
        numbers = [int(n) for pair in p_attr.split() for n in pair.split(',')]

        # group clustering idiom
        points = list(zip(*[iter(numbers)] * 2))

        return np.array((points), dtype=np.uint32)


def text_line_factory(xml_data, min_len, reorder):
    """Create text_lines from given structured data"""

    text_lines = []
    ns_prefix = _determine_namespace(xml_data)
    if 'alto' in ns_prefix:
        text_lines = get_alto_lines(xml_data, ns_prefix, min_len)
    elif ns_prefix in ('page2013', 'page2019'):
        text_lines = get_page_lines(xml_data, ns_prefix, min_len, reorder)

    # proceed only valid lines
    return [t for t in text_lines if t.valid]


def get_alto_lines(xml_data, ns_prefix, min_len):
    all_lines = xml_data.findall(f'.//{ns_prefix}:TextLine', XML_NS)
    all_lines_len = [l for l in all_lines if len(' '.join(
        [s.attrib['CONTENT'] for s in l.findall(f'{ns_prefix}:String', XML_NS)])) >= min_len]
    return [ALTOLine(line, ns_prefix) for line in all_lines_len]


def get_page_lines(xml_data, ns_prefix, min_len, reorder):
    all_lines = xml_data.findall(f'.//{ns_prefix}:TextLine', XML_NS)
    matchings = []
    for textline in all_lines:
        text_equiv = textline.find(
            f'{ns_prefix}:TextEquiv/{ns_prefix}:Unicode', XML_NS)
        if text_equiv.text:
            stripped = text_equiv.text.strip()
            if len(stripped) and len(stripped) >= min_len:
                matchings.append(textline)
        else:
            words = textline.findall(
                f'{ns_prefix}:Word/{ns_prefix}:TextEquiv/{ns_prefix}:Unicode', XML_NS)
            if len(words):
                msg = f"[{xml_data.base}] no text but words for line '{textline.attrib['id']}'"
                raise RuntimeError(msg)
    return [PageLine(line, ns_prefix, reorder) for line in matchings]


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

    def __init__(self, path_ocr_data, path_image_data, output_dir):
        if not isinstance(path_ocr_data, str):
            path_ocr_data = str(path_ocr_data)
        self._pair_prefix = None
        self.path_ocr_data = path_ocr_data
        self.xml_data = etree.parse(path_ocr_data).getroot()
        if path_image_data is not None and not isinstance(path_image_data, str):
            path_image_data = str(path_image_data)
        self.path_image_data = path_image_data
        if not self.path_image_data:
            self._resolve_image_path(path_ocr_data)
        self.image_data = load_image(self.path_image_data)
        self.output_dir = output_dir
        self.xdpi = None
        self.ydpi = None
        (self.xdpi, self.ydpi) = read_dpi(self.path_image_data)

    @property
    def pair_prefix(self) -> str:
        """label for pair files"""

        if self._pair_prefix is None:
            _raw_label = Path(self.path_ocr_data).stem
            if _raw_label.isnumeric():
                self._pair_prefix = f'page{int(_raw_label)}'
            else:
                self._pair_prefix = _raw_label
        return self._pair_prefix

    @pair_prefix.setter
    def pair_prefix(self, pair_prefix):
        """Set output dir explicitely"""

        self._pair_prefix = pair_prefix

    def _resolve_image_path(self, path_xml_data):
        self.path_image_data = resolve_image_path(path_xml_data)

    def _calculate_tiff_param(self):
        """
        Value '2' means 'inches':
        cf. https://www.loc.gov/preservation/digital/formats/content/tiff_tags.shtml
        """

        if self.xdpi and self.ydpi:
            return [IMWRITE_TIFF_RESUNIT, 2, IMWRITE_TIFF_XDPI, self.xdpi,
                    IMWRITE_TIFF_YDPI, self.ydpi]
        return []

    def create(self, min_chars=DEFAULT_MIN_CHARS,
               summary=False, reorder=False, rotation_threshold=0.1,
               sanitize=True, intrusion_ratio=0.125, binarize=False, padding=0):
        """
        Put training data sets which textlines consist of at least min_chars as
        text-image part pairs starting with prefix into folder_out
        """

        training_datas = text_line_factory(
            self.xml_data, min_len=min_chars, reorder=reorder)

        for training_data in training_datas:
            try:
                self.write_pair(
                    training_data,
                    self.image_data,
                    sanitize=sanitize,
                    intrusion_ratio=intrusion_ratio,
                    rotation_threshold=rotation_threshold,
                    binarize=binarize,
                    padding=padding)
            except ExtractPairException as exc:
                print(f"[ERROR] {exc}' for {training_data.element_id}")

        if summary:
            self.write_summary(training_datas)

        return training_datas

    def write_pair(self, text_line: TextLine,
                   image_handle, sanitize, intrusion_ratio, rotation_threshold, binarize, padding):
        """Serialize training data pairs"""

        _data_label = Path( self.path_ocr_data).stem
        if _data_label.isnumeric():
            _data_label = f'p{int(_data_label)}'
        _dir_path = os.path.join(self.output_dir, self.pair_prefix)
        if not os.path.isdir(_dir_path):
            os.makedirs(_dir_path)
        gt_txt_name = f'{self.pair_prefix}_{_data_label}_{text_line.element_id}{SUFFIX_GT_TXT_}'
        gt_txt_path = os.path.join(_dir_path, gt_txt_name)
        img_name = f'{self.pair_prefix}_{_data_label}_{text_line.element_id}{SUFFIX_GT_IMG_TIF}'
        img_path = os.path.join(_dir_path, img_name)
        content = text_line.get_textline_content()
        img_frame = extract_rectangular_frame(image_handle, text_line)
        if content and img_frame.any():
            # write image
            if sanitize:
                img_frame = sanitize_frame(
                    img_frame, text_line, intrusion_ratio, rotation_threshold, padding)
            if binarize:
                img_frame = binarize_frame(img_frame)
            params = self._calculate_tiff_param()
            if params:
                imwrite(img_path, img_frame, params)
            else:
                imwrite(img_path, img_frame)
            # write text file
            with open(gt_txt_path, 'w', encoding="utf8") as fhdl:
                fhdl.write(content)
        else:
            _msg = f"Can't extract pair {gt_txt_path}/{img_path} for {text_line}"
            raise ExtractPairException(_msg)

    def write_summary(self, training_datas: List):
        """Serialize training data pairs"""

        contents = [d.get_textline_content() + '\n' for d in training_datas]
        file_name = self.pair_prefix + SUFFIX_SUMMARY
        file_path = os.path.join(self.output_dir, self.pair_prefix, file_name)
        with open(file_path, 'w', encoding="utf8") as fhdl:
            fhdl.writelines(contents)


def calculate_grayscale(low=168, neighbourhood=32, in_data=None):
    """
    Calculate the_gray via fixed limits or from given in_data
    return triple (low, high, mean)
    """
    nb_center = int(neighbourhood/2)
    if in_data is None:
        return (low, low+neighbourhood, low+nb_center)
    if in_data is not None and len(in_data) > 0:
        ref = calc_reference(in_data)
        the_low = int(ref - nb_center)
        the_high = int(ref + nb_center)
        return (the_low, the_high, the_low+nb_center)


def gray_canvas(w, h, low=168, bound=8, in_data=None):
    """
    Create the_gray Canvas with given dimension and range or
    calculate range from in_data
    """
    (start, end, _) = calculate_grayscale(low, bound, in_data)
    the_raw = np.random.randint(start, end, (h, w)).astype(np.uint8)
    kernel = np.ones((5, 5), np.float32)/25
    return filter2D(the_raw, -1, kernel)


def calc_reference(arr, the_threshold=127):
    """Calc reference val after removing background below threshold (default: split by middle)"""
    filt = arr > the_threshold
    filt_arr = arr[filt]
    return np.median(filt_arr)


def shape_to_box(the_shape):
    """
    Calculate bounding box
    """
    p1 = np.min(the_shape, axis=0)
    p2 = np.max(the_shape, axis=0)
    return (p1[0], p1[1], p2[0], p2[1])


def is_rectangular(a_shape) -> bool:
    """
    The bounding box will always be greater or equals than enclosed polygon
    https://stackoverflow.com/questions/62467829/python-check-if-shapely-polygon-is-a-rectangle
    """
    (_, _, angle) = minAreaRect(np.array(a_shape, dtype=np.float32))
    return angle == 90.0


def extract_rectangular_frame(image_handle, text_line):
    """
    Cut frame if it is rectangular, otherwise mask shape
    and merge it with background
    """
    the_shape = text_line.shape
    start_h = text_line.shape[0][0]
    start_v = text_line.shape[0][1]
    end_h = text_line.shape[2][0]
    end_v = text_line.shape[2][1]
    if not is_rectangular(the_shape):
        (start_h, start_v, end_h, end_v) = shape_to_box(the_shape)
    frame = image_handle[start_v:end_v, start_h:end_h]
    # create new copy in memory, otherwise strange artefacts
    # occour in preceeding lines
    return frame.copy()


def sanitize_frame(image_frame, text_line, intrusion_ratio, rotation_threshold, padding):
    """Apply several curation tasks on textline image"""

    # remove intruders from top and bottom
    (san_frame, _, _) = clear_vertical_borders(image_frame, intrusion_ratio)

    # fit text_line to specific polygonal shape
    the_shape = text_line.shape
    if not is_rectangular(the_shape):
        san_frame = fit_to_shape(san_frame, the_shape)

    # optional central rotation of text line
    san_frame = rotate_text_line_center(san_frame, rotation_threshold)[0]

    # optional padding
    if padding > 0:
        san_frame = add_padding(san_frame, padding)

    return san_frame


def get_centroid_y(shape):
    """Calculate shape centroid via image momentum"""
    M = moments(shape)
    divis = 1 if M['m00'] == 0 else M['m00']
    return int(M['m01']/divis)


def clear_vertical_borders(image_frame, intrusion_ratio):
    """
    Clear vertical overlappings by:
    * binarize blurred input image data
    * drawing artificial border
    * collect only contours that touch this
    * get contours that are specific ratio to close to the edge
    * fill those with specific grey tone
    """
    thresh = binarize_frame(image_frame)
    img = copyMakeBorder(
        thresh, 1, 1, 1, 1, BORDER_CONSTANT, None, (255))
    contours, _ = findContours(img, RETR_TREE, CHAIN_APPROX_SIMPLE)
    (top_edge, btm_edge) = calculate_intrusion_aware_edge(
        img.shape, intrusion_ratio)
    top_cnts = [c for c in contours if 0 in c]
    top_intruders = [c for c in top_cnts if get_centroid_y(c) <= top_edge]
    btm_cnts = [c for c in contours if img.shape[0]-1 in c]
    btm_intruders = [c for c in btm_cnts if get_centroid_y(c) >= btm_edge]
    invasores = top_intruders + btm_intruders
    if len(invasores) > 0:
        the_gray = calculate_grayscale(in_data=image_frame)
        # scale slightly up
        scaled = [resize(i.astype(np.float32), None,
                             fx=1.49, fy=1.49) for i in invasores]
        scaled_pts = [s.astype(np.int32) for s in scaled]
        fillPoly(image_frame, pts=scaled_pts,
                     color=(the_gray), lineType=LINE_AA)
    return (image_frame, len(top_intruders), len(btm_intruders))


def calculate_intrusion_aware_edge(img_shape, intrusion_ratio):
    """Calculate top and bottom edges of intrusion aware areas"""
    height = img_shape[0]
    if isinstance(intrusion_ratio, list):
        return (int(height * intrusion_ratio[0]), int(height - height * intrusion_ratio[1]))
    return (int(height * intrusion_ratio), int(height - height * intrusion_ratio))


def binarize_frame(image_frame):
    """Binarization with binary and otsu"""
    blurred = GaussianBlur(image_frame, (3, 3), 0)
    thresh_flags = THRESH_BINARY + THRESH_OTSU
    thresh = threshold(blurred, 0, 255, thresh_flags)
    return thresh[1]


def fit_to_shape(image_frame, shape_coords):
    """
    Get polygonal shape from image_frame by:
    * translate shape coords to fit frame
    * create polygonal mask from shape coords
    * create the_gray canvas as background
    * apply masked image to background
    """
    pts = np.array(shape_coords, dtype=np.int32)
    (x, y, w, h) = boundingRect(pts)
    # translate coords
    pts = pts - [x, y]
    # create boolean mask where pixel color != 0
    mask = np.zeros((image_frame.shape))
    fillConvexPoly(mask, pts, 1)
    mask = mask.astype(bool)
    # reduce w/h since the refer to the bounding/enclosing box
    the_canvas = gray_canvas(w-1, h-1, in_data=image_frame)
    # apply mask
    the_canvas[mask] = image_frame[mask]
    return the_canvas


def rotate_text_line_center(img, rotation_threshold=0.1, max_angle=10.0):
    """
    Determine possible center rotation by dominant line orientation
    * ensure img data has grayscale shape
    * detect edges
    * determine probalistic hough lines on edges
    * transform lines to vector+angle form
    * filter lines with to high angle (misfits)
    * calculate afterwards mean angle
    * check if mean angle is above rotation threshold:
      only if so, enhance img to prevent rotation
      black area artifacts with constant padding
    * rotate
    * slice rotation result due previous padding
    """
    angle = None
    if img.ndim == 3:
        img = np.mean(img, -1).astype(np.uint8)
    edges = Canny(img, 100, 300, 5)
    min_len = img.shape[1] / 4
    max_gap = min_len
    min_votes = int(img.shape[0] / 2)
    lines = HoughLinesP(edges, 1, np.pi/180, min_votes,
                            minLineLength=min_len, maxLineGap=max_gap)
    if lines is None:
        return (img, angle)
    ptn_quads = [(m[0], m[1], m[2], m[3])
                 for l in np.take(lines, [0, 1, 2, 3], axis=2) for m in l]
    angs = [math.atan2(x2-x1, y2-y1) * 180 / np.pi for x1,
            y1, x2, y2 in ptn_quads]
    fit_angles = [a for a in angs if (abs(90.0-a) < max_angle)]
    mean_angle = np.mean(fit_angles)
    if abs(90.0 - mean_angle) >= rotation_threshold:
        angle = 90.0 - mean_angle
        center = image_center(img)
        M = getRotationMatrix2D(center, angle, 1.0)
        img = add_padding(img, 50)
        img = warpAffine(img, M, img.shape[1::-1], flags=INTER_LINEAR)
        img = img[50:-50, 50:-50]

    return (img, angle)


def image_center(image):
    M = moments(image)
    divis = 1 if M['m00'] == 0 else M['m00']
    return (int(M["m10"] / divis), int(M['m01'] / divis))


def add_padding(image_frame, p):
    """
    Additional padding in every orientation
    between existing image content and borders
    """
    (_, _, clr) = calculate_grayscale(in_data=image_frame)
    return copyMakeBorder(image_frame, p, p, p, p, BORDER_CONSTANT, None, value=clr)


def load_image(path_image_data):
    return imread(path_image_data, IMREAD_GRAYSCALE)


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


def read_dpi(path_image_data):
    """Determine DPI from Image metadata"""

    if str(path_image_data).endswith(".tif"):
        return read_dpi_from_tif(path_image_data)
    elif str(path_image_data).endswith(".jpg") or str(path_image_data).endswith(".png"):
        with Image.open(path_image_data) as image_file:
            if 'dpi' in image_file.info:
                x_dpi, y_dpi = image_file.info['dpi']
                return (int(x_dpi), int(y_dpi))
    return (DEFAULT_DPI, DEFAULT_DPI)


def coords_center(coord_tokens):
    """Calculate Shape center from textual represented coordinates data"""
    vals = [int(b) for a in map(lambda e: e.split(','), coord_tokens) for b in a]
    point_pairs = list(zip(*[iter(vals)]*2))
    return tuple(map(lambda c: sum(c) / len(c), zip(*point_pairs)))


def to_center_coords(elem, namespace, vertical=False):
    coords = elem.find(f'{namespace}:Coords', XML_NS)
    coord_tokens = coords.attrib['points'].split()
    if len(coord_tokens) > 0:
        center = coords_center(coord_tokens)
        if vertical:
            return center[1]
        return center[0]
