import os

import cv2
import numpy as np

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import sys
import boto3
from io import BytesIO

ACCESS_ID = os.environ.get('ACCESS_ID')
SECRET_KEY = os.environ.get('SECRET_KEY')
BUCKET_NAME = os.environ.get('BUCKET_NAME')

s3 = boto3.client('s3', aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY)


def add_objects(weights_file, cfg_file, classes, video_key):

    net = cv2.dnn.readNet(weights_file, cfg_file)
    response = s3.get_object(Bucket=BUCKET_NAME, Key=video_key)
    img = response['Body'].read()
    nparray = cv2.imdecode(np.asarray(bytearray(img)), cv2.IMREAD_COLOR)
    cap = cv2.VideoCapture(nparray)

    font = cv2.FONT_HERSHEY_PLAIN
    colors = np.random.uniform(0, 255, size=(100, 3))

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    out = cv2.VideoWriter('boxed.mp4', fourcc, 30, (frame_width, frame_height))

    df = pd.DataFrame(columns=['frame', 'id', 'type', 'x', 'y', 'w', 'h', 'conf'])

    frame = 0
    while frame < 100:
        _, img = cap.read()
        height, width, _ = img.shape

        blob = cv2.dnn.blobFromImage(img, 1/255, (416, 416), (0,0,0), swapRB=True, crop=False)
        net.setInput(blob)
        output_layers_names = net.getUnconnectedOutLayersNames()
        layerOutputs = net.forward(output_layers_names)

        boxes = []
        confidences = []
        class_ids = []

        for output in layerOutputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.2:
                    center_x = int(detection[0]*width)
                    center_y = int(detection[1]*height)
                    w = int(detection[2]*width)
                    h = int(detection[3]*height)

                    x = int(center_x - w/2)
                    y = int(center_y - h/2)

                    boxes.append([x, y, w, h])
                    confidences.append((float(confidence)))
                    class_ids.append(class_id)


        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.2, .4)
        if len(indexes) > 0:
            for i in indexes.flatten():
                x, y, w, h = boxes[i]
                label = str(classes[class_ids[i]])
                confidence = str(round(confidences[i],2))
                df = pd.concat([df, pd.DataFrame({'frame':frame, 'id': class_ids[i], 'type': label, 'x': x, 'y': y, 'w': w, 'h': h, 'conf': round(confidences[i],2)}, index=[0])], ignore_index=True)
                color = colors[i]
                cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                cv2.putText(img, label + " " + confidence, (x, y + 20), font, 2, (255, 255, 255), 2)
            out.write(img)
        frame += 1
    return df


if __name__ == "__main__":
    df = add_objects('yolov4-rds_best_2000.weights', 'yolov4-rds.cfg', ["1", '2', '3', '4'], '1f499952.mp4')
    print(df)
