#!/bin/bash
mkdir crefl_sw
cd crefl_sw
curl -O ftp://drl-fs-1.sci.gsfc.nasa.gov/.SOFTWARE/.CVIIRS_SPA_V1.0/CVIIRS_1.0_SPA_1.0.tar.gz
curl -O ftp://drl-fs-1.sci.gsfc.nasa.gov/.SOFTWARE/.CVIIRS_SPA_V1.0/CVIIRS_1.0_SPA_1.0_PATCH_1.tar.gz
tar -zxf CVIIRS_1.0_SPA_1.0.tar.gz
tar -zxf CVIIRS_1.0_SPA_1.0_PATCH_1.tar.gz
mv SPA/CVIIRS/algorithm/CVIIRS cviirs
mv SPA/CVIIRS/algorithm/PREPROCESS preprocess
mkdir tarfiles
mv *.tar.gz tarfiles
rm -rf SPA
