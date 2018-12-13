#!/usr/bin/env python

import numpy as np
from numpy.linalg import norm, inv
from bvec_rotation import read_bvecs, read_bvals
import argparse
import os, warnings, sys
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import nibabel as nib

PRECISION= 17
np.set_printoptions(precision= PRECISION)

def bvec_scaling(bval, bvec, b_max):
    
    if bval:
        factor= np.sqrt(bval/b_max)
        if norm(bvec)!=factor:
            bvec= np.array(bvec)*factor

    # bvec= [str(np.round(x, precision)) for x in bvec]
    bvec= [str(x) for x in bvec]

    return ('   ').join(bvec)


def matrix_string(A):
    # A= np.array(A)
    
    A= str(A.tolist())
    A= A.replace(', ',',')
    A= A.replace('],[',') (')
    return '('+A[2:-2]+')'
    
def rotation_matrix(hdr):

    b= hdr['quatern_b']
    c= hdr['quatern_c']
    d= hdr['quatern_d']
    a= np.sqrt(1.0-(b*b+c*c+d*d))

    R = np.array([[a*a + b*b - c*c - d*d, 2*b*c - 2*a*d, 2*b*d + 2*a*c],
                  [2*b*c + 2*a*d, a*a + c*c - b*b - d*d, 2*c*d - 2*a*b],
                  [2*b*d - 2*a*c, 2*c*d + 2*a*b, a*a + d*d - c*c - b*b]])

    return R

def main():

    parser = argparse.ArgumentParser(description='NIFTI to NHDR conversion tool setting byteskip = -1')
    parser.add_argument('--nifti', type=str, required=True, help='nifti file')
    parser.add_argument('--bval', type=str, required=True, help='bval file')
    parser.add_argument('--bvec', type=str, required=True, help='bvec file')
    parser.add_argument('--nhdr', type=str, required=True, help='output nhdr file')

    args = parser.parse_args()

    if args.nifti.endswith('.gz'):
        encoding = 'gzip'
    elif args.nifti.endswith('.nii'):
        encoding = 'raw'
    else:
        raise ValueError('Invalid nifti file')

    img= nib.load(args.nifti)
    hdr= img.header

    if not args.nhdr.endswith('.nhdr'):
        args.nhdr+='.nhdr'

    f= open(args.nhdr, 'w')
    console= sys.stdout
    sys.stdout= f
    

    dim= hdr['dim'][0]
    print(f'NRRD0005\n# This nhdr file was generated by pnl.bwh.harvard.edu pipeline\n\
# See https://github.com/pnlbwh for more info\n\
# Complete NRRD file format specification at:\n\
# http://teem.sourceforge.net/nrrd/format.html\n\
type: short\ndimension: {dim}\nspace: right-anterior-superior')

    sizes= hdr['dim'][1:dim+1]
    print('sizes: {}'.format((' ').join(str(x) for x in sizes)))

    spc_dir= hdr.get_qform()[0:3,0:3].T

    # most important key
    print('byteskip: -1')

    print(f'endian: little\nencoding: {encoding}')
    print('space units: "mm" "mm" "mm"')

    spc_orig= hdr.get_qform()[0:3,3]
    print('space origin: ({})'.format((',').join(str(x) for x in spc_orig)))

    print('data file: ', args.nifti)

    if dim==4:
        print(f'space directions: {matrix_string(spc_dir)} none')
        print('centerings: cell cell cell ???')
        print('kinds: space space space list')
        # R= rotation_matrix(hdr)
        # mf = R @ np.diag([1, 1, hdr['pixdim'][0]])
        mf = spc_dir @ inv(np.diag(hdr['pixdim'][1:4]))
        print(f'measurement frame: {matrix_string(mf)}')

        bvecs = read_bvecs(args.bvec)
        bvals = read_bvals(args.bval)

        print('modality:=DWMRI')

        b_max = max(bvals)
        print(f'DWMRI_b-value:={b_max}')
        for ind in range(len(bvals)):
            scaled_bvec = bvec_scaling(bvals[ind], bvecs[ind], b_max)
            print(f'DWMRI_gradient_{ind:04}:={scaled_bvec}')

    else:
        print(f'space directions: {matrix_string(spc_dir)}')
        print('centerings: cell cell cell')
        print('kinds: space space space')

        
    f.close()
    sys.stdout= console


if __name__ == '__main__':
    main()
