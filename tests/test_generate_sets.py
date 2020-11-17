# -*- coding: utf-8 -*-
"""Specifications for Generation of training data sets"""

import os
import pathlib
import shutil

import numpy as np
import lxml.etree as etree

from cv2 import cv2

import pytest

from sets.training_sets import (
    TrainingData,
    XML_NS
)

RES_ROOT = os.path.join('tests', 'resources')


def generate_image(path_image, words, columns, rows, params=None):
    """Generate synthetic in-memory image data"""

    arr_floats = np.random.rand(columns, rows) * 255
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
    elif ns_prefix == 'page2013':
        page_words = root.findall(f'.//{ns_prefix}:Word', XML_NS)
        for page_word in page_words:
            txt = page_word.find('.//page2013:Unicode', XML_NS).text
            p1 = page_word.find(
                'page2013:Coords',
                XML_NS).attrib['points'].split()[0]
            origin = (int(p1.split(',')[0]), int(p1.split(',')[1]))
            words.append((origin, txt))

    return words


@pytest.fixture(name='input_alto_tif')
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
        rows=6619,
        columns=9976,
        params=tif_params)

    return str(path)


def test_create_trainingset_from_alto_and_tif(input_alto_tif):
    """Create text-image pairs for tesstrain from given ALTO V3 and tif"""

    path_input_dir = os.path.dirname(input_alto_tif)
    path_input_parent = pathlib.Path(path_input_dir).parent
    path_tif = os.path.join(
        path_input_parent,
        'scan',
        '1667522809_J_0073_0512.tif')
    assert os.path.exists(path_tif)

    training_data = TrainingData(input_alto_tif, path_tif)
    data = training_data.create(min_chars=32, folder_out=path_input_dir)

    # assert
    assert len(data) == 225
    path_items = [p for p in os.listdir(os.path.dirname(input_alto_tif))]
    assert len([tif for tif in path_items if str(tif).endswith(".tif")]) == 225
    assert len([txt for txt in path_items if str(
        txt).endswith(".gt.txt")]) == 226


@pytest.fixture(name='input_page2013_jpg')
def _fixture_page2013_jpg(tmpdir):

    res = os.path.join(RES_ROOT, 'xml', '699723.xml')
    path_page = tmpdir.mkdir('training').join('699723.xml')
    shutil.copyfile(res, path_page)

    words = extract_words(path_page)

    file_path = tmpdir.mkdir('images').join('699723.jpg')

    # 2257x3062px
    generate_image(file_path, words=words, rows=2257, columns=3062)

    return str(path_page)



TXTLINE_699723_TL_1 = '، ةمن حالة إلى حالة ، ومن رتبة إلى رتبة ، أولها بالعفوصة وبعد ذلك بالحموضة'


def test_create_trainingset_from_page2013_and_jpg(input_page2013_jpg):
    """Create text-image pairs for tesstrain from given Page2013 and jpg"""

    path_input_dir = os.path.dirname(input_page2013_jpg)
    path_input_parent = pathlib.Path(path_input_dir).parent
    path_jpg = os.path.join(path_input_parent, 'images', '699723.jpg')
    assert os.path.exists(path_jpg)

    # act
    training_data = TrainingData(input_page2013_jpg, path_jpg)
    data = training_data.create(min_chars=8, folder_out=path_input_dir)

    # assert
    assert len(data) == 25
    path_items = os.listdir(os.path.dirname(input_page2013_jpg))
    assert len([tif for tif in path_items if str(tif).endswith(".tif")]) == 25
    txt_files = sorted(
        [txt for txt in path_items if str(txt).endswith(".gt.txt")])
    assert len(txt_files) == 26

    # assert text orientation, which is in this case invalid
    with open(os.path.join(os.path.dirname(input_page2013_jpg), txt_files[2])) as txt_file:
        arab = txt_file.readline().strip()
        assert arab == TXTLINE_699723_TL_1


# def test_create_trainingset_from_page2013_and_jpg_revert_words(input_page2013_jpg):
#     """
#     Create text-image pairs for tesstrain with right-to-left text orientation like arabic
#     languages from given Page2013 and jpg
#     """

#     path_input_dir = os.path.dirname(input_page2013_jpg)
#     path_input_parent = pathlib.Path(path_input_dir).parent
#     path_jpg = os.path.join(path_input_parent, 'images', '699723.jpg')
#     assert os.path.exists(path_jpg)

#     # act
#     training_data = TrainingData(input_page2013_jpg, path_jpg)
#     data = training_data.create(
#         min_chars=8, folder_out=path_input_dir, rtl=True)

#     # assert
#     assert len(data) == 25
#     path_items = os.listdir(os.path.dirname(input_page2013_jpg))
#     assert len([tif for tif in path_items if str(tif).endswith(".tif")]) == 25
#     txt_files = sorted(
#         [txt for txt in path_items if str(txt).endswith(".gt.txt")])

#     # one more textfile as summary
#     assert len(txt_files) == 26

#     # assert text orientation
#     with open(os.path.join(os.path.dirname(input_page2013_jpg), txt_files[2])) as txt_file:
#         arabic = txt_file.readline().strip()
#         assert arabic == TXTLINE_699723_TL_1_RTL
