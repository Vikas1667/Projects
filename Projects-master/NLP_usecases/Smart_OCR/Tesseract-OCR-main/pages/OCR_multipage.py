import pytesseract
from pdf2image import convert_from_path
import cv2
import os
import streamlit as st
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from PyPDF2 import PdfFileReader, PdfFileWriter
# from data_parsing import pdf_extract
from pathlib import Path
import base64
# importing required modules
import PyPDF2
import tabula
from tabula import read_pdf
from tabulate import tabulate
import pandas as pd


# converts pdf to list of images
def pdf_to_img(pdf):
    pdf_pages = convert_from_path(pdf, dpi=350, poppler_path=r'C:\Program Files\poppler-0.68.0\bin')
    page_no = 1
    img_list = []
    for page in pdf_pages:
        page.save('page' + str(page_no) + '.jpg', 'JPEG')
        img_list.append('page' + str(page_no) + '.jpg')
        page_no += 1
    print('PDF to Image Conversion Successful!')
    return img_list


# each image is processed, contours are plotted and sorted
def bounding_boxes(img_list, show_boxes):
    boxes = {}
    for curr_img in img_list:
        img = cv2.imread(curr_img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, ksize=(9, 9), sigmaX=0)
        # _, thresh = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY)
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 30)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        dilate = cv2.dilate(thresh, kernel, iterations=4)
        contours, _ = cv2.findContours(dilate, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)

        temp = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # print(x, y, w, h)
            if cv2.contourArea(contour) < 10000:
                continue
            temp.append([x, y, w, h])
            if show_boxes:
                cv2.rectangle(img, (x, y), (x + w, y + h), color=(255, 0, 255), thickness=3)
        if show_boxes:
            img = cv2.resize(img, (500, 700), interpolation=cv2.INTER_AREA)
            st.image(image=img, caption=curr_img)
            # cv2.imshow(curr_img, img)
            # cv2.waitKey(0)
        boxes[curr_img] = temp
    print('Contours saved Successfully!')
    return boxes


# text is extracted from each contours stored
def extract_text(boxes):
    pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
    tessdata_dir_config = "--tessdata-dir 'C:/Program Files/Tesseract-OCR/tessdata'"

    text = ''
    for key in boxes:
        img = cv2.imread(key)
        for x, y, w, h in boxes[key]:
            cropped_image = img[y:y + h, x:x + w]
            _, thresh = cv2.threshold(cropped_image, 127, 255, cv2.THRESH_BINARY)
            text += str(pytesseract.image_to_string(thresh, config=tessdata_dir_config))
    print('Text Extraction Completed!')
    return text


# base function
def ocr(filename, show_boxes):
    '''
    :param filename:
    :param show_boxes:
    :return:
    '''
    if filename:
        img_list = pdf_to_img(filename)
        # print(img_list)
        boxes = bounding_boxes(img_list, show_boxes)
        if not show_boxes:
            text = extract_text(boxes)
            # text = 'hii'
            return text
    else:
        st.warning('Please select a PDF file!')


def file_uploader():
    uploaded_file = st.file_uploader(label='Upload PDF', type='pdf')
    return uploaded_file

# def ocr_engine(filename):
# main code

# if __name__ == '__main__':

st.set_page_config(
    page_title="OCR",
    page_icon="👋",
)

# st.set_page_config(page_title="OCR engine", page_icon="📈")

st.title('Text Extraction using OCR')
st.sidebar.success("Select a demo above.")



if 'text' not in st.session_state:
    st.session_state.text = ''

if 'flag' not in st.session_state:
    st.session_state.flag = False


uploaded_file=file_uploader()

if uploaded_file:
    filename = uploaded_file.name
    filename = './input_pdf/' + filename
    row0col1, row0col2 = st.columns([1, 1])
    with row0col1:
        if st.button(label='Run OCR'):
            st.session_state.text = ocr(filename, 0)
            st.session_state.flag = True

        if st.session_state.flag:
            root = Tk()
            root.withdraw()

            # Make folder picker dialog appear on top of other windows
            root.wm_attributes('-topmost', 1)

            if st.button('Save File'):
                dirname = st.text_input('Selected folder:', filedialog.askdirectory(master=root))
                with open(os.path.join(dirname, '../extracted_text.txt'), 'w') as file:
                    file.write(st.session_state.text)
                st.success('File saved successfully!')

    with row0col2:
        if st.button(label='Bounding Box'):
            ocr(filename, 1)


    ## vikas parsing large pdf file

    pdfReader = PyPDF2.PdfFileReader(filename)
    no_of_pages = pdfReader.numPages

    # details
    st.markdown('No of Pages in {} are {}'.format(filename, no_of_pages))

    # can be start other than zero update in next
    user_start_input = st.number_input('enter the start', step=1)
    if no_of_pages > 50:
        segment = st.slider('Exceeding the pages please select the pages ranges', user_start_input, no_of_pages, 5)
        print('s:', segment)
        segments = [user_start_input, segment]

        # start_page, end_page = segment
        if st.button('segment_pdf_save'):
            for segment in segments:
                pdf_writer = PdfFileWriter()

            for page_num in range(user_start_input - 1, segment):
                pdf_writer.addPage(pdfReader.getPage(page_num))

            p = Path(filename)

            # ouput = p.parent / p.with_stem(f'{p.stem}_pages_{user_start_input}-{segment}')
            with open('seg_pdf/NYSE_seg.pdf', 'wb') as out:
                pdf_writer.write(out)
    # end of code

    if st.button('extract table from pdf'):
        tables = read_pdf(filename, pages='all')

        for table in tables:
            table_df = pd.DataFrame(table)
            st.dataframe(table_df)
