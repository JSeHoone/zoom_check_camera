import cv2
import os

def make_atten_book():
        current_path = os.path.expanduser("~") + "\\Downloads\\" # 다운로드 폴더로 가기
        atten_dict = {
            'name' : [],
            'number' : [],
        }

        with open(current_path +'출석부2.txt', 'r', encoding='utf-8') as f:
            atten_list = f.read().split('\n')
            for human in atten_list:
                name, number = human.split('\t')
                atten_dict['name'].append(name)
                atten_dict['number'].append(number)
        return atten_dict   
    
# BGR로 특정 색을 추출하는 함수
def bgrExtraction(image, bgrLower, bgrUpper):
    img_mask = cv2.inRange(image, bgrLower, bgrUpper) 
    result = cv2.bitwise_and(image, image, mask=img_mask) 
    return result

# Tesseract 실행 파일 PATH 가져오기
def find_tess_path():
    os_list = os.environ['PATH'].split(';')
    for i in os_list:
        if 'Tesseract' in i :
            return i