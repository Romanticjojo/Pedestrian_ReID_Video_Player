from flask import Flask, request, jsonify
import torch
import numpy as np
import cv2
from ultralytics import YOLO
import pymysql
import json

# 初始化 Flask 应用
app = Flask(__name__)

# 加载模型
model_detection = YOLO('model1.pt')  # 用于行人检测
model_reid = YOLO('model2.pt')       # 用于行人重识别

# 数据库连接配置
db_config = {
    'host': 'localhost',    # 数据库主机名
    'user': 'your_user',    # 数据库用户名
    'password': 'your_password',  # 数据库密码
    'database': 'your_database'   # 数据库名
}

def connect_db():
    # 连接到 MySQL 数据库并返回连接对象
    return pymysql.connect(**db_config)

def load_image(file):
    # 从上传的文件中读取图像并转换为适合处理的格式
    file_bytes = np.frombuffer(file.read(), np.uint8)  # 将文件读取为字节数组
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)  # 解码为图像
    if image is None:
        raise ValueError("Could not decode image")  # 如果无法解码，抛出异常
    return image

def process_results(results):
    # 处理检测模型的结果，提取出相关信息
    people = []
    for i, box in enumerate(results.boxes):
        xyxy = box.xyxy.tolist()  # 检测框的坐标 [x1, y1, x2, y2]
        confidence = box.confidence.item()  # 检测置信度
        class_id = box.cls.item()  # 类别 ID

        if class_id == 0:  # 仅处理类别 (类 ID 为 0)
            people.append({
                'person_id': i,
                'pos': xyxy,
                'confidence': confidence
            })
    return people

def reid_results(results):
    # 处理重识别模型的结果，提取出相关信息
    reid_data = []
    for i, box in enumerate(results.boxes):
        xyxy = box.xyxy.tolist()  # 检测框的坐标 [x1, y1, x2, y2]
        confidence = box.confidence.item()  # 重识别置信度
        feature_vector = box.feature.tolist()  # 特征向量

        reid_data.append({
            'person_id': i,
            'pos': xyxy,
            'confidence': confidence,
            'features': feature_vector
        })
    return reid_data

def save_detection_to_db(detections):
    # 将检测结果保存到 Detections 表中
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            for person in detections:
                sql = """
                INSERT INTO Detections (person_id, x1, y1, x2, y2, confidence)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (person['person_id'], *person['pos'], person['confidence']))
        conn.commit() 
    finally:
        conn.close()  # 关闭数据库连接

def save_reid_to_db(reid_data):
    # 将重识别结果保存到 Reidentifications 表中
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            for person in reid_data:
                sql = """
                INSERT INTO Reidentifications (person_id, x1, y1, x2, y2, confidence, features)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                # 将特征向量转换为 JSON 格式存储
                cursor.execute(sql, (person['person_id'], *person['pos'], person['confidence'], json.dumps(person['features'])))
        conn.commit() 
    finally:
        conn.close()  # 关闭数据库连接

def check_model_status():
    # 检查模型是否已成功加载
    try:
        # 进行一个简单的推断以确保模型正常工作
        dummy_input = torch.zeros((1, 3, 640, 640))  # 创建一个空的输入张量
        _ = model_detection(dummy_input)
        _ = model_reid(dummy_input)
        return True
    except Exception as e:
        return False, str(e)
    
def reinitialize_mot():
    # 重新初始化多目标跟踪模型
    global model_detection, model_reid
    try:
        # 重新加载模型
        model_detection = YOLO('model1.pt')
        model_reid = YOLO('model2.pt')
        return True, "MOT reinitialized successfully"
    except Exception as e:
        return False, str(e)

def get_person_info(person_id):
    # 从数据库中获取指定 person_id 的信息
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            # 查询 Detections 表中指定 person_id 的信息
            sql = "SELECT * FROM Detections WHERE person_id = %s"
            cursor.execute(sql, (person_id,))
            result = cursor.fetchone()
            if result:
                # 返回的列是 (id, timestamp, person_id, x1, y1, x2, y2, confidence)
                return {
                    'id': result[0],
                    'timestamp': result[1],
                    'person_id': result[2],
                    'pos': [result[3], result[4], result[5], result[6]],
                    'confidence': result[7]
                }
            else:
                return None
    finally:
        conn.close()

# 1. 多目标跟踪接口
@app.route('/mot', methods=['POST'])
def mot():
    # 多目标跟踪接口
    if 'img' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    try:
        img_file = request.files['img']
        image = load_image(img_file)

        # 将图像转换为张量格式
        image_tensor = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        image_tensor = image_tensor.unsqueeze(0)  # 增加批次维度

        # 使用模型进行检测
        results = model_detection(image_tensor)

        # 处理检测结果
        people = process_results(results)

        # 保存检测结果到数据库
        save_detection_to_db(people)

        return jsonify({'info': 'Detection complete', 'people': people})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 2. 行人重识别接口
@app.route('/photo', methods=['POST'])
def photo():
    # 行人重识别接口
    if 'img' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    try:
        img_file = request.files['img']
        image = load_image(img_file)

        # 将图像转换为张量格式
        image_tensor = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        image_tensor = image_tensor.unsqueeze(0)  # 增加批次维度

        # 使用模型进行重识别
        results = model_reid(image_tensor)

        # 处理重识别结果
        reid_data = reid_results(results)

        # 保存重识别结果到数据库
        save_reid_to_db(reid_data)

        return jsonify({'info': 'ReID complete', 'people': reid_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 3. 服务器状态检查接口
@app.route('/ping', methods=['POST'])
def ping():
    model_status, error_message = check_model_status()
    if model_status:
        return jsonify({'status': 'Server is online', 'model_status': 'Models are loaded and operational'})
    else:
        return jsonify({'status': 'Server is online', 'model_status': 'Error loading models', 'error': error_message}), 500


# 4. 重新初始化多目标识别接口
@app.route('/reinit_mot', methods=['POST'])
def reinit_mot():
    # 重新初始化 MOT
    success, message = reinitialize_mot()
    if not success:
        return jsonify({'status': 'Reinitialization failed', 'error': message}), 500

    # 获取并处理图像
    if 'image' not in request.files:
        return jsonify({'status': 'No image provided'}), 400
    
    file = request.files['image']
    try:
        image = load_image(file)
    except ValueError as e:
        return jsonify({'status': 'Invalid image', 'error': str(e)}), 400

    # 执行检测推理
    detection_results = model_detection(image)
    processed_results = process_results(detection_results)

    # 执行重识别推理
    reid_results_data = model_reid(image)
    reid_processed_results = reid_results(reid_results_data)

    return jsonify({
        'status': 'Inference completed',
        'detection_results': processed_results,
        'reid_results': reid_processed_results
    })


# 5. 数据库刷新接口
@app.route('/reinit_query', methods=['POST'])
def reinit_query():
    # 重新初始化数据库
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            # 清空 Detections 和 Reidentifications 表
            cursor.execute("TRUNCATE TABLE Detections")
            cursor.execute("TRUNCATE TABLE Reidentifications")
        conn.commit() 
        return jsonify({'status': 'Query reinitialized successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# 6. 数据库更新接口
@app.route('/update_query', methods=['POST'])
def update_query():
    # 更新数据库中
    data = request.json
    person_id = data.get('person_id')
    new_confidence = data.get('confidence')

    if not person_id or new_confidence is None:
        return jsonify({'error': 'Missing person_id or confidence'}), 400

    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            # 更新 Detections 表中指定 person_id 的 confidence
            sql = "UPDATE Detections SET confidence = %s WHERE person_id = %s"
            cursor.execute(sql, (new_confidence, person_id))
        conn.commit() 
        return jsonify({'status': 'Query updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# 7. 查询特定ID接口
@app.route('/query_id', methods=['GET'])
def query_id():
    # 查询特定 ID
    ids = request.args.getlist('id')
    people_info = []

    for person_id in ids:
        info = get_person_info(person_id)
        if info:
            people_info.append(info)
        else:
            people_info.append({'id': person_id, 'info': 'No information found'})

    return jsonify({'people': people_info})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6060)