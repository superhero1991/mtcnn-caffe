import sys
sys.path.append('.')
sys.path.append('/home/congweilin/caffe/python')
sys.path.append('/usr/lib/python2.7/dist-packages')
import tools
import caffe
import cv2
import numpy as np
deploy = '../12net/12net.prototxt'
caffemodel = '../12net/12net.caffemodel'
net_12 = caffe.Net(deploy,caffemodel,caffe.TEST)
deploy = '../24net/24net.prototxt'
caffemodel = '../24net/24net.caffemodel'
net_24 = caffe.Net(deploy,caffemodel,caffe.TEST)
deploy = '../48net/48net.prototxt'
caffemodel = '../48net/48net.caffemodel'
net_48 = caffe.Net(deploy,caffemodel,caffe.TEST)

def detectFace(img_path,threshold):
    img = cv2.imread(imgpath)
    caffe_img = img.copy()-128
    origin_h,origin_w,ch = caffe_img.shape
    scales = tools.calculateScales(img)
    out = []
    for scale in scales:
        hs = int(origin_h*scale)
        ws = int(origin_w*scale)
        scale_img = cv2.resize(caffe_img,(ws,hs))
        scale_img = np.swapaxes(scale_img, 0, 2)
        net_12.blobs['data'].reshape(1,3,ws,hs)
        net_12.blobs['data'].data[...]=scale_img
        out.append(net_12.forward())
    image_num = len(scales)
    rectangles = []
    for i in range(image_num):    
        cls_prob = out[i]['cls_score'][0][1]
        roi_prob = out[i]['roi_score'][0]
        out_h,out_w = cls_prob.shape
        out_side = max(out_h,out_w)
        rectangle = tools.detect_face_12net(cls_prob,roi_prob,out_side,1/scales[i],origin_w,origin_h,threshold[0])
        rectangles.extend(rectangle)
    rectangles = tools.NMS(rectangles,0.3,'iou')
    if len(rectangles)==0:
        return rectangles
    net_24.blobs['data'].reshape(len(rectangles),3,24,24)
    crop_number = 0
    for rectangle in rectangles:
        crop_img = caffe_img[rectangle[1]:rectangle[3], rectangle[0]:rectangle[2]]
        scale_img = cv2.resize(crop_img,(24,24))
        scale_img = np.swapaxes(scale_img, 0, 2)
        net_24.blobs['data'].data[crop_number] =scale_img 
        crop_number += 1
    out = net_24.forward()
    cls_prob = out['cls_score']
    roi_prob = out['roi_score']
    rectangles = tools.filter_face_24net(cls_prob,roi_prob,rectangles,origin_w,origin_h,threshold[1])
    if len(rectangles)==0:
        return rectangles
    net_48.blobs['data'].reshape(len(rectangles),3,48,48)
    crop_number = 0
    for rectangle in rectangles:
        crop_img = caffe_img[rectangle[1]:rectangle[3], rectangle[0]:rectangle[2]]
        scale_img = cv2.resize(crop_img,(48,48))
        scale_img = np.swapaxes(scale_img, 0, 2)
        net_48.blobs['data'].data[crop_number] =scale_img 
        crop_number += 1
    out = net_48.forward()
    cls_prob = out['cls_score']
    roi = out['roi']
    pts = out['pts']
    rectangles = tools.filter_face_48net(cls_prob,roi,pts,rectangles,origin_w,origin_h,threshold[2])
    return rectangles



imgpath = ""
rectangles = detectFace(imgpath,threshold)
img = cv2.imread(imgpath)
draw = img.copy()
for rectangle in rectangles:
    cv2.putText(draw,str(rectangle[14]),(int(rectangle[0]),int(rectangle[1])),cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0))
    cv2.rectangle(draw,(int(rectangle[0]),int(rectangle[1])),(int(rectangle[2]),int(rectangle[3])),(255,0,0),1)
cv2.imshow("12net",draw)
cv2.waitKey()

