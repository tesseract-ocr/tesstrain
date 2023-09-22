# -*- coding: utf-8 -*-
"""Specification for Generation of training data sets"""

# disable warnings from fixture names
# pylint: disable=redefined-outer-name

import os
import pathlib
import shutil

from cv2 import (
    imread,
    imwrite,
    putText,
    FONT_HERSHEY_COMPLEX,
    IMREAD_UNCHANGED,
    IMWRITE_TIFF_RESUNIT,
    IMWRITE_TIFF_XDPI,
    IMWRITE_TIFF_YDPI,
)
import numpy as np
import pytest
import lxml.etree as etree

from tesstrain import (
    TrainingSets,
    gray_canvas,
    read_dpi,
    calculate_grayscale,
    clear_vertical_borders,
    rotate_text_line_center,
    coords_center,
    XML_NS
)

RES_ROOT = os.path.join('tests', 'resources')

GT_SUFFIX = '.gt.txt'
OCR_TRANSK = '288652'
OCR_TRANSK_IMAG = f'{OCR_TRANSK}.jpg'
OCR_TRANSK_DATA = f'{OCR_TRANSK}.xml'
OCR_D_RESULT_01 = 'OCR-RESULT_0001'
OCR_D_PAGE_DATA = f'{OCR_D_RESULT_01}.xml'
OCR_DATA_729422 = '729422'
OCR_DATA_PERSIAN = 'Lubab_alAlbab.pdf_000003'

# data problem: just TextLines, no Words at all
OCR_DATA_RAM110 = 'ram110'

# data problem: empty TextLine, although Words with text exist
OCR_FID_ERR_1123596 = '1123596'

IMG_GEN_MAX = 224
IMG_GEN_MIN = 168


def generate_image(path_image, words, columns, rows, params=None):
    """Generate synthetic in-memory greyscale image data"""

    dst = gray_canvas(columns, rows, IMG_GEN_MIN, IMG_GEN_MAX)
    if words:
        for word in words:
            render_text = word[1]
            origin = (word[0][0] + 10, word[0][1] + 10)
            dst = putText(
                dst, render_text, origin, FONT_HERSHEY_COMPLEX, 1.0, (0, 0, 0), 3, bottomLeftOrigin=False)

    imwrite(str(path_image), dst, params)
    return path_image


def extract_words(path_xml_data):
    """
    Get origin and textdata for all words in path_data
    * if word granularity available, use words
    * else if no words, use text lines
    * else return empty list
    """

    texts = []
    root = etree.parse(str(path_xml_data)).getroot()
    root_tag = root.xpath('namespace-uri(.)')
    ns_prefix = [k for (k, v) in XML_NS.items() if v == root_tag][0]
    if 'alto' in ns_prefix:
        strings = root.findall(f'.//{ns_prefix}:String', XML_NS)
        texts = [((int(s.attrib['HPOS']), int(s.attrib['VPOS'])),
                  s.attrib['CONTENT']) for s in strings]
    elif ns_prefix in ('page2013', 'page2019'):
        text_elements = root.findall(f'.//{ns_prefix}:Word', XML_NS)

        # if no words available, go for textlines
        if not text_elements:
            text_elements = root.findall(f'.//{ns_prefix}:TextLine', XML_NS)

        texts = _extract_texts(text_elements, ns_prefix)

    return texts


def _extract_texts(elements, ns_prefix):
    texts = []
    for element in elements:
        txt = element.find(f'.//{ns_prefix}:Unicode', XML_NS).text
        points = element.find(f'{ns_prefix}:Coords',
                              XML_NS).attrib['points'].split()
        if points:
            p1 = points[0]
            origin = (int(p1.split(',')[0]), int(p1.split(',')[1]))
            texts.append((origin, txt))

    return texts


@pytest.fixture
def fixture_newspaper_p512(tmpdir):
    res_alto = os.path.join(RES_ROOT, 'xml', '1667522809_J_0073_0512.xml')
    path = tmpdir.mkdir('training').join('1667522809_J_0073_0512.xml')
    shutil.copyfile(res_alto, path)

    words = extract_words(path)

    file_path = tmpdir.mkdir('scan').join('1667522809_J_0073_0512.tif')
    tif_params = [
        IMWRITE_TIFF_RESUNIT, 2,
        IMWRITE_TIFF_XDPI, 300,
        IMWRITE_TIFF_YDPI, 300
    ]

    # 6619x9976px
    generate_image(
        file_path,
        words=words,
        columns=6619,
        rows=9976,
        params=tif_params)

    return str(path)


def test_create_sets_from_alto_and_tif(fixture_newspaper_p512):
    """Create text-image pairs from ALTO V3 and TIF"""

    output_dir = os.path.dirname(fixture_newspaper_p512)
    path_input_parent = pathlib.Path(output_dir).parent
    path_tif = os.path.join(
        path_input_parent,
        'scan',
        '1667522809_J_0073_0512.tif')
    assert os.path.exists(path_tif)

    _t_sets = TrainingSets(fixture_newspaper_p512, path_tif, output_dir)
    data = _t_sets.create(min_chars=32, summary=True, padding=5)

    # assert
    assert len(data) == 225
    _output_dir = os.path.join(output_dir, '1667522809_J_0073_0512')
    path_items = os.listdir(_output_dir)
    tifs = [tif for tif in path_items if str(tif).endswith(".tif")]
    assert len(tifs) == 225
    # please no *.gt.tif !!
    assert not [tif for tif in path_items if str(tif).endswith(".gt.tif")]
    lines = [txt for txt in path_items if str(txt).endswith(GT_SUFFIX)]

    # one more txt since summery
    assert len(lines) == 226


@pytest.fixture
def fixture_page2013_jpg(tmpdir):

    res = os.path.join(RES_ROOT, 'xml', OCR_TRANSK_DATA)
    path_page = tmpdir.mkdir('training').join(OCR_TRANSK_DATA)
    shutil.copyfile(res, path_page)

    words = extract_words(path_page)

    file_path = tmpdir.mkdir('images').join(OCR_TRANSK_IMAG)

    # 2257x3062px
    generate_image(file_path, words=words, columns=2091, rows=2938)

    return str(path_page)


def test_create_sets_from_page2013_and_jpg(fixture_page2013_jpg):
    """
    Create text-image pairs from PAGE2013 and JPG with defaults
    From 33 Textlines one got dropped because in only contained 3 chars
    and min_chars was set to '8'
    """

    path_input_dir = os.path.dirname(fixture_page2013_jpg)
    path_input_parent = pathlib.Path(path_input_dir).parent
    path_image = os.path.join(path_input_parent, 'images', OCR_TRANSK_IMAG)
    assert os.path.exists(path_image)

    # act
    training_data = TrainingSets(fixture_page2013_jpg, path_image, output_dir=path_input_dir)
    training_data.pair_prefix = OCR_TRANSK
    data = training_data.create(min_chars=8, summary=True)

    # assert
    assert len(data) == 32
    _output_dir = os.path.join(path_input_dir, f'{OCR_TRANSK}')
    path_items = os.listdir(_output_dir)
    assert len([tif for tif in path_items if str(tif).endswith(".tif")]) == 32
    txt_files = sorted(
        [txt for txt in path_items if str(txt).endswith(GT_SUFFIX)])

    # additional summary written, therefore we have one more txt
    assert len(txt_files) == 33

    # assert mixed content
    with open(os.path.join(_output_dir, txt_files[1]), encoding='utf-8') as txt_file:
        arab = txt_file.readline().strip()
        assert 'XIX' in arab


def test_create_sets_from_page2013_and_jpg_no_summary(
        fixture_page2013_jpg):
    """Create text-image pairs from PAGE2013 and JPG without summary"""

    path_input_dir = os.path.dirname(fixture_page2013_jpg)
    path_input_parent = pathlib.Path(path_input_dir).parent
    path_image = os.path.join(path_input_parent, 'images', OCR_TRANSK_IMAG)
    assert os.path.exists(path_image)

    # act
    training_data = TrainingSets(fixture_page2013_jpg, path_image, output_dir=path_input_dir)
    data = training_data.create(min_chars=3, summary=False, reorder=True)

    # assert
    expected_len = 33
    assert len(data) == expected_len
    _output_dir = os.path.join(path_input_dir, f'page{OCR_TRANSK}')
    path_items = os.listdir(_output_dir)
    tifs = [tif for tif in path_items if str(tif).endswith(".tif")]
    assert len(tifs) == expected_len
    txt_files = [txt for txt in path_items if str(txt).endswith(GT_SUFFIX)]
    assert len(txt_files) == expected_len

    # no summary written, no extra txt file
    assert len(txt_files) == expected_len


@pytest.fixture
def fixture_page2019_png(tmpdir):

    res = os.path.join(RES_ROOT, 'xml', OCR_D_PAGE_DATA)
    path_page = tmpdir.mkdir('training').join(OCR_D_PAGE_DATA)
    shutil.copyfile(res, path_page)

    words = extract_words(path_page)

    file_path = tmpdir.mkdir('images').join('OCR-RESULT_0001.png')

    # 2257x3062px
    generate_image(file_path, words=words, columns=2164, rows=2448)

    return str(path_page)


def test_create_sets_from_page2019_and_png(fixture_page2019_png):
    """
    Create text-image pairs from PAGE2013 and JPG without summary
    From total 35 lines 2 got dropped because they contain less
    than min_len = 8 chars
    """

    path_input_dir = os.path.dirname(fixture_page2019_png)
    path_input_parent = pathlib.Path(path_input_dir).parent
    path_image = os.path.join(
        path_input_parent,
        'images',
        'OCR-RESULT_0001.png')
    assert os.path.exists(path_image)

    # act
    training_data = TrainingSets(fixture_page2019_png, path_image, output_dir=path_input_dir)
    data = training_data.create(min_chars=8, summary=True)

    # assert
    expected_len = 33
    assert len(data) == expected_len
    _output_dir = os.path.join(path_input_dir, f'{OCR_D_RESULT_01}')
    path_items = os.listdir(_output_dir)
    tifs = [tif for tif in path_items if str(tif).endswith(".tif")]
    assert len(tifs) == expected_len

    txt_files = [txt for txt in path_items if str(txt).endswith(GT_SUFFIX)]

    # summary written
    assert len(txt_files) == 34


@pytest.fixture
def fixture_ocrd_workspace(tmpdir):
    res = os.path.join(RES_ROOT, 'xml', OCR_D_PAGE_DATA)
    path_page = tmpdir.mkdir('OCR-RESULT').join(OCR_D_PAGE_DATA)
    shutil.copyfile(res, path_page)
    words = extract_words(path_page)
    file_path = tmpdir.mkdir('OCR-D-IMG-PNG').join('OCR-D-IMG-PNG_0001.png')
    generate_image(file_path, words=words, columns=2164, rows=2448)
    return str(path_page)


def test_create_sets_from_ocrd_workdspace(fixture_ocrd_workspace):
    """Create Training data with default OCR-D-Workspace"""

    # arrange
    path_input_dir = os.path.dirname(fixture_ocrd_workspace)

    # act
    training_data = TrainingSets(fixture_ocrd_workspace, None, output_dir=path_input_dir)
    data = training_data.create(min_chars=8)

    # assert
    assert len(data) == 33


@pytest.fixture
def fixture_ocrd_workspace_invalid(tmpdir):
    res = os.path.join(RES_ROOT, 'xml', OCR_D_PAGE_DATA)
    path_page = tmpdir.mkdir('OCR-RESULT').join(OCR_D_PAGE_DATA)
    shutil.copyfile(res, path_page)
    return str(path_page)


def test_create_sets_from_ocrd_workdspace_fails(fixture_ocrd_workspace_invalid):
    """Create Training data fails because OCR-D-Workspace misses image"""

    # act
    with pytest.raises(RuntimeError) as excinfo:
        TrainingSets(fixture_ocrd_workspace_invalid, None, '/home')

    # assert
    assert 'invalid image_path' in str(excinfo.value)


@pytest.fixture
def fixture_invalid_coords(tmpdir):
    res = os.path.join(RES_ROOT, 'xml', f'{OCR_DATA_729422}.xml')
    path_page = tmpdir.join(f'{OCR_DATA_729422}.xml')
    shutil.copyfile(res, path_page)
    words = extract_words(path_page)
    file_path = tmpdir.join(f'{OCR_DATA_729422}.jpg')
    generate_image(file_path, words=words, columns=2251, rows=3049)
    return str(tmpdir)


def test_handle_invalid_coords(fixture_invalid_coords):
    """When procesing data with invalid coords, raise Error"""

    # arrange
    ocr_data = os.path.join(fixture_invalid_coords, f'{OCR_DATA_729422}.xml')
    img_data = os.path.join(fixture_invalid_coords, f'{OCR_DATA_729422}.jpg')
    training_data = TrainingSets(ocr_data, img_data, output_dir=fixture_invalid_coords)

    # act
    with pytest.raises(RuntimeError) as exc:
        training_data.create()

    # assert: one line was skipped
    expected = "Invalid Coords of Word 'word_1595308100448_546' in 'tl_13'!"
    assert expected == str(exc.value)


@pytest.fixture(name='fixture_page_devanagari')
def _fixture_page_devanagari(tmpdir):

    res = os.path.join(RES_ROOT, 'xml', f'{OCR_DATA_RAM110}.xml')
    path_page = tmpdir.join(f'{OCR_DATA_RAM110}.xml')
    shutil.copyfile(res, path_page)
    words = extract_words(path_page)
    file_path = tmpdir.join(f'{OCR_DATA_RAM110}.png')
    generate_image(file_path, words=words, columns=3873, rows=5848)
    return str(tmpdir)


def test_handle_page_devanagari_with_textlines(fixture_page_devanagari):
    """When procesing invalid coords, skip pair and alert user"""

    # arrange
    ocr_data = os.path.join(fixture_page_devanagari, f'{OCR_DATA_RAM110}.xml')
    img_data = os.path.join(fixture_page_devanagari, f'{OCR_DATA_RAM110}.png')
    training_data = TrainingSets(ocr_data, img_data, output_dir=fixture_page_devanagari)

    # act
    data = training_data.create(summary=True)

    # assert
    assert len(data) == 24
    assert 'tl_24' in [l.element_id for l in data]
    assert 'tl_25' not in [l.element_id for l in data]


@pytest.fixture
def fixture_alto4_persian(tmpdir):

    res = os.path.join(RES_ROOT, 'xml', f'{OCR_DATA_PERSIAN}.xml')
    path_page = tmpdir.join(f'{OCR_DATA_PERSIAN}.xml')
    shutil.copyfile(res, path_page)
    words = extract_words(path_page)
    file_path = tmpdir.join(f'{OCR_DATA_PERSIAN}.png')
    generate_image(file_path, words=words, columns=1500, rows=2401)
    return str(tmpdir)


def test_handle_alto4_persian_without_strange_strings(fixture_alto4_persian):
    """
    Process data from OpenITI
    https://raw.githubusercontent.com/OpenITI/OCR_GS_Data/master/TypeFaces/persian_intertype/data/
    """

    # arrange
    ocr_data = os.path.join(fixture_alto4_persian, f'{OCR_DATA_PERSIAN}.xml')
    img_data = os.path.join(fixture_alto4_persian, f'{OCR_DATA_PERSIAN}.png')
    training_data = TrainingSets(ocr_data, img_data, output_dir=fixture_alto4_persian)

    # act
    data = training_data.create(summary=True)

    # assert
    assert len(data) == 23
    assert 'eSc_line_23302' in [l.element_id for l in data]


@pytest.fixture
def page_1123596(tmp_path):
    """
    Represents data with a single empty TextLine, although there are single Words with content
    Unclear origin; maybe synchronization problem when working with Transkribus
    """

    res = os.path.join(RES_ROOT, 'xml', f'{OCR_FID_ERR_1123596}.xml')
    path_page = tmp_path / f'{OCR_FID_ERR_1123596}.xml'
    shutil.copyfile(res, path_page)
    words = extract_words(path_page)
    file_path = tmp_path / f'{OCR_FID_ERR_1123596}.png'
    generate_image(file_path, words=words, columns=593, rows=950)
    return str(tmp_path)


def test_error_1123596(page_1123596):
    """When OCR-Data contains empty lines, although words are present, yield Exception"""

    # arrange
    ocr_data = os.path.join(page_1123596, f'{OCR_FID_ERR_1123596}.xml')
    img_data = os.path.join(page_1123596, f'{OCR_FID_ERR_1123596}.png')
    training_data = TrainingSets(ocr_data, img_data, output_dir=page_1123596)

    # act
    with pytest.raises(RuntimeError) as exc:
        training_data.create()

    # assert
    assert "no text but words for line 'line_1617688885509_1198'" in str(
        exc.value)


def test_calculate_greyscale_simple():
    """Create greyscale value from plain boundaries"""

    # act
    (l, h, c) = calculate_grayscale(192, 16)

    # assert
    assert l == 192
    assert h == 208
    assert c == 200


@pytest.fixture
def rowimage_0251_0011_tl36(tmp_path):
    res = pathlib.Path(RES_ROOT) / 'img' / '1681877805_J_0011_0251_tl_36.tif'
    assert os.path.isfile(res)
    path_img = tmp_path / 'tl_36.tif'
    shutil.copyfile(res, path_img)
    image_frame = imread(str(path_img), IMREAD_UNCHANGED)

    # check original image data distribution back - foreground
    # 17.236 gray val <= 128 foreground, 161.594 brighter as background
    (_, bins, vals) = np.unique((image_frame > 128),
                                return_counts=True, return_index=True)
    assert len(bins) == 2
    assert vals[0] == 35981
    assert vals[1] == 142849
    # top intruder
    assert image_frame[0][94] == 48
    # bottom intruder
    assert image_frame[89][1936] == 91

    return image_frame


def test_calculate_grayscale_from_frame(rowimage_0251_0011_tl36):

    # act
    (l, h, c) = calculate_grayscale(in_data=rowimage_0251_0011_tl36)

    # assert
    assert l == 212
    assert h == 244
    assert c == 228


def test_remove_intruders_0251_tl36(rowimage_0251_0011_tl36):
    """
    Test intruder remove with real world newspaper textline
    Saalezeitung (PPN 1681877805) film 0011, page 0251, tl_36
    """

    # arrange
    assert rowimage_0251_0011_tl36.shape == (90, 1987)

    # act
    (img, intruder_top, intruder_btm) = clear_vertical_borders(
        rowimage_0251_0011_tl36, 0.125)

    # assert shape stays the same
    assert img.shape == (90, 1987)
    # change of previous top intruder to the brighter side
    assert img[0][94] == 212
    # change of previous bottom intruder to the brighter side
    assert img[89][1936] == 212
    assert intruder_top == 6
    assert intruder_btm == 14

    # re-check dark and bright distribution of fore-and
    # background *after* sanitizing: dark regions have
    # been decreased, bright pixels grow accordingly
    (_, bins, vals) = np.unique((img > 127), return_counts=True, return_index=True)
    assert len(bins) == 2
    assert vals[0] == 35109  # 35981 < 35109
    assert vals[1] == 143721  # 143721 > 142849


@pytest.fixture
def rowimage_0251_0011_tl04(tmp_path):
    res = pathlib.Path(RES_ROOT) / 'img' / \
        '1681877805_J_0011_0251_tl_4_clean.tif'
    assert os.path.isfile(res)
    path_img = tmp_path / 'tl_4.tif'
    shutil.copyfile(res, path_img)
    image_frame = imread(str(path_img), IMREAD_UNCHANGED)

    # check original image data distribution back - foreground
    (_, bins, vals) = np.unique((image_frame > 127),
                                return_counts=True, return_index=True)
    assert len(bins) == 2
    assert vals[0] == 41742
    assert vals[1] == 254058
    return image_frame


def test_no_intruders_0251_tl04_clean(rowimage_0251_0011_tl04):
    """
    Test intruder remove with real world newspaper textline
    Saalezeitung (PPN 1681877805) film 0011, page 0251, tl_36
    """

    # arrange
    assert rowimage_0251_0011_tl04.shape == (145, 2040)

    # act
    (img, intruder_top, intruder_btm) = clear_vertical_borders(
        rowimage_0251_0011_tl04, 0.125)

    # assert shape stays the same
    assert img.shape == (145, 2040)
    assert intruder_top == 0
    assert intruder_btm == 0

    # re-check dark and bright distribution of fore-and
    # background *after* sanitizing: no change
    (_, _, vals) = np.unique((img > 127), return_counts=True, return_index=True)
    assert vals[0] == 41742
    assert vals[1] == 254058


@pytest.fixture
def rowimage_inclined(tmp_path):
    res = pathlib.Path(RES_ROOT) / 'img' / 'LINE_099_tl_407.png'
    assert os.path.isfile(res)
    path_img = tmp_path / 'LINE_099_tl_407.png'
    shutil.copyfile(res, path_img)
    image_frame = imread(str(path_img), IMREAD_UNCHANGED)
    return image_frame


def test_textline_rotated(rowimage_inclined):

    # act
    (_, delta) = rotate_text_line_center(rowimage_inclined)

    # assert
    assert delta == pytest.approx(-0.2, abs=0.1)


def test_read_metadata_png():

    res = pathlib.Path(RES_ROOT) / 'img' / 'LINE_099_tl_407.png'

    # assert
    assert read_dpi(res) == (72, 72)


def test_read_metadata_tif():

    res = pathlib.Path(RES_ROOT) / 'img' / '1681877805_J_0011_0251_tl_4.tif'

    # assert
    assert read_dpi(res) == (470, 470)


def test_read_metadata_jpg():

    res = pathlib.Path(RES_ROOT) / 'img' / '1681877805_J_0011_0251_tl_4.jpg'

    # assert
    assert read_dpi(res) == (470, 470)


def test_coords_empty():

    assert () == coords_center([])


@pytest.mark.parametrize("in_data,expected", [
    (['100, 100', '200, 200'], (150, 150)),
    (['1673,576', '1863,605', '1879,589', '1935,601', '2015,558', '2063,602', '2190,603', '2258,587', '2259,464', '2155,443', '2036,455', '2016,474', '1673,472'], (2001.1, 540.7))])
def test_coords_center(in_data, expected):

    # assert
    result = coords_center(in_data)
    assert result[0] == pytest.approx(expected[0], abs=0.1)
    assert result[1] == pytest.approx(expected[1], abs=0.1)
