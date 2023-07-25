import sys
import re
import cv2
import numpy as np
import pytesseract
import datetime
import mouse
from PIL import ImageGrab
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton
from function import make_atten_book,bgrExtraction,find_tess_path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # layout size 고정하기
        self.setGeometry(0,0,350,50)

        # self.path_ 를 만들기 위한 함수 실행
        self.path_ = find_tess_path()

        self.setWindowTitle("실시간 카메라 유무 확인")
        
        self.layout1 = QVBoxLayout()
        self.layout2 = QVBoxLayout()
        self.layout3 = QVBoxLayout()
        
        self.label1 = QLabel("Tesseract 실행 파일 위치를 적어주세요.")
        self.layout1.addWidget(self.label1)
        
        self.label2 = QLabel("수강생들이 보이는 화면을 캡쳐하듯 드래그하세요.")
        self.layout2.addWidget(self.label2)
        
        self.label3 = QLabel("현재 카메라를 키지 않은 사람")
        self.layout3.addWidget(self.label3)
        
        self.widget1 = QWidget()
        self.widget1.setLayout(self.layout1)
        
        self.widget2 = QWidget()
        self.widget2.setLayout(self.layout2)
        
        self.widget3 = QWidget()
        self.widget3.setLayout(self.layout3)
        
        self.current_widget = self.widget1  # 현재 표시되는 위젯 설정
        self.setCentralWidget(self.current_widget)
        
        self.path_input = QLineEdit()
        self.path_input.setText(f'{self.path_}'+ '\\tesseract.exe')
        self.layout1.addWidget(self.path_input)
        
        self.start_button = QPushButton("시작")
        self.capture_button = QPushButton("캡쳐")
        self.start_button.clicked.connect(self.start_processing)
        self.capture_button.clicked.connect(self.capture_and_process)
        self.layout1.addWidget(self.start_button)
        self.layout2.addWidget(self.capture_button)
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_image)
        
    def start_processing(self):
        path = self.path_input.text()
        pytesseract.pytesseract.tesseract_cmd = path
        self.config = ('-l kor --oem 3 --psm 13')
        
        # 출석부 만들기
        self.atten_dict = make_atten_book()

        ####      
        self.current_widget = self.widget2
        self.setCentralWidget(self.current_widget)
        # self.timer.start(1000) # 1초마다 이미지 전처리 수행
    
    def capture_and_process(self):
        # 영역 캡쳐하기
        self.set_roi()
        
        # 이미지 캡처 및 처리 수행
        self.process_image()

        # 이벤트 루프 처리를 위해 QApplication.processEvents() 호출
        while not ROI_SET:
            QApplication.processEvents()
        
    def process_image(self):
        self.timer.start(5000) # 5초마다 이미지 전처리 수행
        ## 이미지 전처리 부분
        bgrLower = np.array([26, 26, 26])    # 추출할 색의 하한
        bgrUpper = np.array([28, 30, 32])    # 추출할 색의 상한

        image = cv2.cvtColor(np.array(ImageGrab.grab(bbox=(x1, y1, x2, y2))), cv2.COLOR_BGR2RGB)

        bgrResult = bgrExtraction(image, bgrLower, bgrUpper)

        blur = cv2.GaussianBlur(bgrResult, ksize=(5,5), sigmaX=0)
        edged = cv2.Canny(blur,3,75)

        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        atten_list_index = []

        ## 출석부를 참고해서 사번이 없는 경우
        for data in list(contours):
            x = []
            y = []
            for a in data:
                x.append(a[0][0])
                y.append(a[0][1])
            crop_img = image[ max(y)-20 : max(y) , min(x)+5 : min(x) + 125 ] # 이름까지 전체
            gray_roi= cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
            gray_roi = np.where(gray_roi > 120, gray_roi, 0) # 주변은 검게 만들기


            
          
            number = re.sub(r'[^0-9]', '', pytesseract.image_to_string(gray_roi,config=self.config).rstrip())[:8] # 사번은 8자리
            name = name = re.sub(r"[^ㄱ-ㅣ가-힣\s]", "", pytesseract.image_to_string(gray_roi, config = self.config).rstrip()).strip()
            if number in self.atten_dict['number']:
                atten_list_index.append(self.atten_dict['number'].index(number))
            elif name in self.atten_dict['name']:
                atten_list_index.append(self.atten_dict['name'].index(name))
            # if number == '':
            #     name = pytesseract.image_to_string(gray_roi,config=self.config).rstrip()
            #     print(name)
            #     if name in self.atten_dict['name']:
            #         atten_list_index.append(self.atten_dict['name'].index(number)) # 출석 한 사람 atten list에 넣기
            # else:
            #     if number in self.atten_dict['number']:
            #         atten_list_index.append(self.atten_dict['number'].index(number)) # 출석 한 사람 atten list에 넣기

        answer = str()
        cnt = 0
        for i in range(len(self.atten_dict['number'])):
            if cnt == 5:
                answer += '\n'
                cnt = 0
            if i not in atten_list_index:
                answer += self.atten_dict['name'][i]+'\t'
                cnt += 1

        ##### text 전개 부분
        now = str(datetime.datetime.now())
        self.current_widget = self.widget3
        self.label3.setText(now + '\n' + answer)
        self.setCentralWidget(self.current_widget)
        # self.timer.stop()

    ## ROI부분 드래그 하기
    def set_roi(self):
        global ROI_SET, x1, y1, x2, y2
        while(mouse.is_pressed() == False):
            x1, y1 = mouse.get_position()
            while(mouse.is_pressed() == True):
                x2, y2 = mouse.get_position()
                while(mouse.is_pressed() == False):
                    ROI_SET = True
                    return

    

if __name__ == '__main__':
    ROI_SET = False
    x1, y1, x2, y2 = 0, 0, 0, 0

    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
