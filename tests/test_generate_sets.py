# -*- coding: utf-8 -*-
"""Specification for Generation of training data sets"""

import os
import pathlib
import shutil

from sets.training_sets import (
    TrainingSets,
    XML_NS
)

from cv2 import (
    cv2
)
import pytest
import numpy as np
import lxml.etree as etree

RES_ROOT = os.path.join('tests', 'resources')


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
    """Get origin and textdata for all words in path_data"""

    words = []
    root = etree.parse(str(path_xml_data)).getroot()
    root_tag = root.xpath('namespace-uri(.)')
    ns_prefix = [k for (k, v) in XML_NS.items() if v == root_tag][0]
    if 'alto' in ns_prefix:
        strings = root.findall(f'.//{ns_prefix}:String', XML_NS)
        words = [((int(s.attrib['HPOS']), int(s.attrib['VPOS'])),
                  s.attrib['CONTENT']) for s in strings]
    elif ns_prefix in ('page2013', 'page2019'):
        page_words = root.findall(f'.//{ns_prefix}:Word', XML_NS)
        for page_word in page_words:
            txt = page_word.find(f'.//{ns_prefix}:Unicode', XML_NS).text
            p1 = page_word.find(
                f'{ns_prefix}:Coords',
                XML_NS).attrib['points'].split()[0]
            origin = (int(p1.split(',')[0]), int(p1.split(',')[1]))
            words.append((origin, txt))

    return words


@pytest.fixture(name='fixture_alto_tif')
def _fixture_alto_tif(tmpdir):
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
    data = training_data.create(min_chars=32, folder_out=path_input_dir)

    # assert
    assert len(data) == 225
    path_items = os.listdir(os.path.dirname(fixture_alto_tif))
    tifs = [tif for tif in path_items if str(tif).endswith(".tif")]
    assert len(tifs) == 225
    lines = [txt for txt in path_items if str(txt).endswith(".gt.txt")]

    # one more txt since summery
    assert len(lines) == 226


@pytest.fixture(name='fixture_page2013_jpg')
def _fixture_page2013_jpg(tmpdir):

    res = os.path.join(RES_ROOT, 'xml', '288652.xml')
    path_page = tmpdir.mkdir('training').join('288652.xml')
    shutil.copyfile(res, path_page)

    words = extract_words(path_page)

    file_path = tmpdir.mkdir('images').join('288652.jpg')

    # 2257x3062px
    generate_image(file_path, words=words, columns=2091, rows=2938)

    return str(path_page)


def test_create_sets_from_page2013_and_jpg(fixture_page2013_jpg):
    """Create text-image pairs from PAGE2013 and JPG with defaults"""

    path_input_dir = os.path.dirname(fixture_page2013_jpg)
    path_input_parent = pathlib.Path(path_input_dir).parent
    path_image = os.path.join(path_input_parent, 'images', '288652.jpg')
    assert os.path.exists(path_image)

    # act
    training_data = TrainingSets(fixture_page2013_jpg, path_image)
    data = training_data.create(
        min_chars=8,
        folder_out=path_input_dir,
        revert=True)

    # assert
    assert len(data) == 32
    path_items = os.listdir(os.path.dirname(fixture_page2013_jpg))
    assert len([tif for tif in path_items if str(tif).endswith(".tif")]) == 32
    txt_files = sorted(
        [txt for txt in path_items if str(txt).endswith(".gt.txt")])

    # additional summary written
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
    path_image = os.path.join(path_input_parent, 'images', '288652.jpg')
    assert os.path.exists(path_image)

    # act
    training_data = TrainingSets(fixture_page2013_jpg, path_image)
    data = training_data.create(
        min_chars=8,
        folder_out=path_input_dir,
        summary=False, revert=True)

    # assert
    expected_len = 32
    assert len(data) == expected_len
    path_items = os.listdir(os.path.dirname(fixture_page2013_jpg))
    tifs = [tif for tif in path_items if str(tif).endswith(".tif")]
    assert len(tifs) == expected_len
    txt_files = [txt for txt in path_items if str(txt).endswith(".gt.txt")]
    assert len(txt_files) == expected_len

    # no summary written
    assert len(txt_files) == 32


@pytest.fixture(name='fixture_page2019_png')
def _fixture_page2019_png(tmpdir):

    res = os.path.join(RES_ROOT, 'xml', 'OCR-RESULT_0001.xml')
    path_page = tmpdir.mkdir('training').join('OCR-RESULT_0001.xml')
    shutil.copyfile(res, path_page)

    words = extract_words(path_page)

    file_path = tmpdir.mkdir('images').join('OCR-RESULT_0001.png')

    # 2257x3062px
    generate_image(file_path, words=words, columns=2164, rows=2448)

    return str(path_page)


def test_create_sets_from_page2019_and_png(fixture_page2019_png):
    """Create text-image pairs from PAGE2013 and JPG without summary"""

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
        min_chars=8,
        folder_out=path_input_dir)

    # assert
    expected_len = 33
    assert len(data) == expected_len
    path_items = os.listdir(os.path.dirname(fixture_page2019_png))
    tifs = [tif for tif in path_items if str(tif).endswith(".tif")]
    assert len(tifs) == expected_len

    txt_files = [txt for txt in path_items if str(txt).endswith(".gt.txt")]

    # summary written
    assert len(txt_files) == 34
