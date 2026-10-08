"""Preserve thin foliage on studio turnarounds before semantic masking.

Only a near-neutral, light border enables this path. Background-connected
pixels are removed; enclosed light coat/cloth pixels remain foreground.
Complex photographs return None and continue through rembg.
"""
import numpy as np
from PIL import Image
from scipy.ndimage import binary_propagation


def studio_foreground(image):
    rgba=np.asarray(image.convert('RGBA')).copy()
    if np.any(rgba[:,:,3]<255):return image.convert('RGBA'), 'provided_alpha'
    rgb=rgba[:,:,:3].astype(np.float32)
    h,w=rgb.shape[:2];margin=max(2,min(h,w)//40)
    border=np.concatenate([rgb[:margin].reshape(-1,3),rgb[-margin:].reshape(-1,3),
        rgb[:,:margin].reshape(-1,3),rgb[:,-margin:].reshape(-1,3)])
    neutral=(border.min(axis=1)>215)&(np.ptp(border,axis=1)<18)
    if neutral.mean()<.92:return None,'semantic_background'
    color=np.median(border[neutral],axis=0)
    eligible=(np.max(np.abs(rgb-color),axis=2)<48)&(np.ptp(rgb,axis=2)<26)
    seed=np.zeros((h,w),bool);seed[0,:]=True;seed[-1,:]=True;seed[:,0]=True;seed[:,-1]=True
    background=binary_propagation(seed&eligible,mask=eligible)
    subject=~background
    ys,xs=np.where(subject)
    if not len(xs) or subject.mean()<.005 or subject.mean()>.90:return None,'semantic_background'
    if (xs.max()-xs.min())<w*.08 or (ys.max()-ys.min())<h*.08:return None,'semantic_background'
    rgba[:,:,3]=subject.astype(np.uint8)*255
    return Image.fromarray(rgba),'neutral_border_flood_fill'
