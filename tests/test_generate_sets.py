# -*- coding: utf-8 -*-
"""Specification for Generation of training data sets"""

# disable warnings from fixture names
# pylint: disable=redefined-outer-name

import os
import pathlib
import shutil

from cv2 import (
    cv2
)
import pytest
import numpy as np
import lxml.etree as etree

from generate_sets import (
    TrainingSets,
    XML_NS
)

RES_ROOT = os.path.join('tests', 'resources')

GT_SUFFIX = '.gt.txt'
OCR_TRANSK_IMAG = '288652.jpg'
OCR_TRANSK_DATA = '288652.xml'
OCR_D_PAGE_DATA = 'OCR-RESULT_0001.xml'
OCR_DATA_729422 = '729422'
OCR_DATA_PERSIAN = 'Lubab_alAlbab.pdf_000003'

# data problem: just TextLines, no Words at all
OCR_DATA_RAM110 = 'ram110'

# data problem: empty TextLine, although Words with text exist
OCR_FID_ERR_1123596 = '1123596'


def generate_image(path_image, words, columns, rows, params=None):
    """Generate synthetic in-memory image data"""

    arr_floats = np.random.rand(rows, columns) * 255
    arr_ints = arr_floats.astype(np.uint8)
    if words:
        for word in words:
            render_text = word[1]
            origin = (word[0][0] + 10, word[0][1] + 10)
            arr_ints = cv2.putText(
                arr_ints, render_text, origin, cv2.FONT_HERSHEY_COMPLEX, 1.0, (0, 0, 0), 3, bottomLeftOrigin=False)

    cv2.imwrite(str(path_image), arr_ints, params)
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
def fixture_alto_tif(tmpdir):
    res_alto = os.path.join(RES_ROOT, 'xml', '1667522809_J_0073_0512.xml')
    path = tmpdir.mkdir('training').join('1667522809_J_0073_0512.xml')
    shutil.copyfile(res_alto, path)

    words = extract_words(path)

    file_path = tmpdir.mkdir('scan').join('1667522809_J_0073_0512.tif')
    tif_params = [
        cv2.IMWRITE_TIFF_RESUNIT,
        2,
        cv2.IMWRITE_TIFF_XDPI,
        300,
        cv2.IMWRITE_TIFF_YDPI,
        300]

    # 6619x9976px
    generate_image(
        file_path,
        words=words,
        columns=6619,
        rows=9976,
        params=tif_params)

    return str(path)


def test_create_sets_from_alto_and_tif(fixture_alto_tif):
    """Create text-image pairs from ALTO V3 and TIF"""

    path_input_dir = os.path.dirname(fixture_alto_tif)
    path_input_parent = pathlib.Path(path_input_dir).parent
    path_tif = os.path.join(
        path_input_parent,
        'scan',
        '1667522809_J_0073_0512.tif')
    assert os.path.exists(path_tif)

    training_data = TrainingSets(fixture_alto_tif, path_tif)
    data = training_data.create(
        min_chars=32, folder_out=path_input_dir, summary=True)

    # assert
    assert len(data) == 225
    path_items = os.listdir(os.path.dirname(fixture_alto_tif))
    tifs = [tif for tif in path_items if str(tif).endswith(".tif")]
    assert len(tifs) == 225
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
    training_data = TrainingSets(fixture_page2013_jpg, path_image)
    data = training_data.create(
        min_chars=8, folder_out=path_input_dir, summary=True, reorder=True)

    # assert
    assert len(data) == 32
    path_items = os.listdir(os.path.dirname(fixture_page2013_jpg))
    assert len([tif for tif in path_items if str(tif).endswith(".tif")]) == 32
    txt_files = sorted(
        [txt for txt in path_items if str(txt).endswith(GT_SUFFIX)])

    # additional summary written, therefore we have one more txt
    assert len(txt_files) == 33

    # assert mixed content
    with open(os.path.join(os.path.dirname(fixture_page2013_jpg), txt_files[2])) as txt_file:
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
    training_data = TrainingSets(fixture_page2013_jpg, path_image)
    data = training_data.create(
        min_chars=3, folder_out=path_input_dir, summary=False, reorder=True)

    # assert
    expected_len = 33
    assert len(data) == expected_len
    path_items = os.listdir(os.path.dirname(fixture_page2013_jpg))
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
    training_data = TrainingSets(fixture_page2019_png, path_image)
    data = training_data.create(
        min_chars=8, summary=True,
        folder_out=path_input_dir)

    # assert
    expected_len = 33
    assert len(data) == expected_len
    path_items = os.listdir(os.path.dirname(fixture_page2019_png))
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
    training_data = TrainingSets(fixture_ocrd_workspace, None)
    data = training_data.create(min_chars=8, folder_out=path_input_dir)

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
        TrainingSets(fixture_ocrd_workspace_invalid, None)

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
    training_data = TrainingSets(ocr_data, img_data)

    # act
    with pytest.raises(RuntimeError) as exc:
        training_data.create(folder_out=fixture_invalid_coords)

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


def test_handle_page_devanagari_with_texlines(fixture_page_devanagari):
    """When procesing invalid coords, skip pair and alert user"""

    # arrange
    ocr_data = os.path.join(fixture_page_devanagari, f'{OCR_DATA_RAM110}.xml')
    img_data = os.path.join(fixture_page_devanagari, f'{OCR_DATA_RAM110}.png')
    training_data = TrainingSets(ocr_data, img_data)

    # act
    data = training_data.create(
        folder_out=fixture_page_devanagari, summary=True)

    # assert
    assert len(data) == 24
    assert 'tl_24' in [l.element_id for l in data]
    assert not 'tl_25' in [l.element_id for l in data]


@pytest.fixture
def fixture_alto4_persian(tmpdir):

    res = os.path.join(RES_ROOT, 'xml', f'{OCR_DATA_PERSIAN}.xml')
    path_page = tmpdir.join(f'{OCR_DATA_PERSIAN}.xml')
    shutil.copyfile(res, path_page)
    words = extract_words(path_page)
    file_path = tmpdir.join(f'{OCR_DATA_PERSIAN}.png')
    generate_image(file_path, words=words, columns=593, rows=950)
    return str(tmpdir)


def test_handle_alto4_persian_without_strange_strings(fixture_alto4_persian):
    """
    Process data from OpenITI
    https://raw.githubusercontent.com/OpenITI/OCR_GS_Data/master/TypeFaces/persian_intertype/data/
    """

    # arrange
    ocr_data = os.path.join(fixture_alto4_persian, f'{OCR_DATA_PERSIAN}.xml')
    img_data = os.path.join(fixture_alto4_persian, f'{OCR_DATA_PERSIAN}.png')
    training_data = TrainingSets(ocr_data, img_data)

    # act
    data = training_data.create(
        folder_out=fixture_alto4_persian, summary=True)

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
    training_data = TrainingSets(ocr_data, img_data)

    # act
    with pytest.raises(RuntimeError) as exc:
        training_data.create(folder_out=page_1123596)

    # assert
    assert "no text but words for line 'line_1617688885509_1198'" in str(
        exc.value)
