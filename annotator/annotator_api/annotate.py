from matplotlib import image as mtp_image
from PIL import Image
import torch
import numpy as np
import cv2
import os
import torch.nn as nn
import copy

class cnn(nn.Module):
    def __init__(self, subRegionHeight, subRegionWidth):
        super(cnn,self).__init__()
        self.cnn_model = nn.Sequential(
            nn.Conv2d(1, 10, (subRegionHeight, subRegionWidth), padding = ((subRegionHeight-1)//2, (subRegionWidth-1)//2)),
            nn.ReLU(),
            nn.Conv2d(10, 1, 1, padding = (0, 0)),
            nn.ReLU())
    def forward(self, x):
        x = self.cnn_model(x)
        x = x.view(x.size(0), -1)
        return x

def findBoundingBoxes(label, subRegionHeight, subRegionWidth):
    boundingBoxes = []
    label = label/np.max(label)
    imageHeight = label.shape[-2]
    imageWidth = label.shape[-1]
    for i in range(label.shape[0]):
        for j in range(label.shape[1]):
            if(label[i][j] >= 0.5):
                boundingBoxes.append([label[i][j], max(0,j-(subRegionWidth//2)), max(0,i-(subRegionHeight//2)), min(imageWidth,j+(subRegionWidth//2)), min(imageHeight,i+(subRegionHeight//2))])
    
    return boundingBoxes

def testModel(model, x, device):
    model.to(device)
    testX = [x]
    testX = np.stack(testX)
    testX = torch.from_numpy(testX)
    testX=testX.type(torch.float32)
    testX = testX.to(device)
    out = model(testX)
    yPred = out[0].detach().cpu().numpy()
    yPred = yPred.reshape(x.shape[1], x.shape[2])
    yPred = yPred/np.max(yPred)
    yPred = yPred*255
    yPred[yPred < 0] = 0
    yPred = yPred.astype(np.uint8)
    return yPred


def annotate(image_path, modelList, document, user):
    image = mtp_image.imread(image_path)
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = 255 - image
    image[image < 127] = 0
    image[image >= 127] = 255

    image = image.reshape((1,image.shape[0],image.shape[1]))
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    result = {}
    for model in modelList:
        anno_model = cnn(int(model.avgHeight), int(model.avgWidth))
        if torch.cuda.is_available():
            anno_model.load_state_dict(torch.load(model.model), strict=False)
        else:
            anno_model.load_state_dict(torch.load(model.model, map_location = torch.device('cpu')), strict=False)

        pred = testModel(anno_model, image, device)
        boundingBoxes = findBoundingBoxes(pred, int(model.avgHeight), int(model.avgWidth))
        for resultAnnotation in boundingBoxes:
            topX = int(resultAnnotation[1])
            topY = int(resultAnnotation[2])
            bottomX = int(resultAnnotation[3])
            bottomY = int(resultAnnotation[4])
            if model.name in result:
                result[model.name].append({
                    'name': model.name,
                    'topX': topX,
                    'topY': topY,
                    'bottomX': bottomX,
                    'bottomY': bottomY,
                    'ground_truth': False,
                    'document': document,
                    'user': user
                })
            else:
                result[model.name] = [{
                    'name': model.name,
                    'topX': topX,
                    'topY': topY,
                    'bottomX': bottomX,
                    'bottomY': bottomY,
                    'ground_truth': False,
                    'document': document,
                    'user': user
                }]
    return result