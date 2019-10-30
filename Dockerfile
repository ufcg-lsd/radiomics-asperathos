FROM sconecuratedimages/issre2019:tensorscone as tensorscone
FROM sconecuratedimages/issre2019:runtime-alpine3.7 as base

RUN apk add --update --no-cache \
    python2 python2-dev py2-pip gcc g++

COPY --from=tensorscone /tensorflow-1.8.0-cp27-cp27mu-linux_x86_64.whl /tmp/

# Install TensorFlow
RUN pip install -U pip setuptools \
 && pip install /tmp/tensorflow-1.8.0-cp27-cp27mu-linux_x86_64.whl \
 && rm -rf /tmp/tensorflow-1.8.0-cp27-cp27mu-linux_x86_64.whl

# Add Edge repos & install required packages
RUN echo -e "\n\
@edgemain http://nl.alpinelinux.org/alpine/edge/main\n\
@edgecomm http://nl.alpinelinux.org/alpine/edge/community\n\
@edgetest http://nl.alpinelinux.org/alpine/edge/testing"\
    >> /etc/apk/repositories \
 && apk add --no-cache --update \
    bash \
    build-base \
    ca-certificates \
    clang-dev \
    clang \
    cmake \
    coreutils \
    curl \
    freetype-dev \
    ffmpeg-dev \
    ffmpeg-libs \
    g++ \
    git \
    gettext \
    lcms2-dev \
    libavc1394-dev \
    libc-dev \
    libffi-dev \
    libjpeg-turbo-dev \
    libpng-dev \
    libressl-dev \
    libtbb@edgetest \
    libtbb-dev@edgetest \
    libwebp-dev \
    linux-headers \
    make \
    musl \
    openblas@edgecomm \
    openblas-dev@edgecomm \
    openblas \
    openblas-dev \
    openjpeg-dev \
    openssl \
    tiff-dev \
    unzip \
    zlib-dev

# Download & Build OpenCV
RUN mkdir -p /opt && cd /opt \
 && wget https://github.com/opencv/opencv/archive/4.0.0.zip \
 && unzip 4.0.0.zip && rm 4.0.0.zip \
 && wget https://github.com/opencv/opencv_contrib/archive/4.0.0.zip \
 && unzip 4.0.0.zip && rm 4.0.0.zip \
 && cd /opt/opencv-4.0.0 && mkdir build && cd build \
 && cmake -D CMAKE_BUILD_TYPE=RELEASE \
        -D CMAKE_C_COMPILER=/usr/bin/gcc \
        -D CMAKE_CXX_COMPILER=/usr/bin/g++ \
        -D CMAKE_INSTALL_PREFIX=/usr/local \
        -D OPENCV_EXTRA_MODULES_PATH=/opt/opencv_contrib-4.0.0/modules \
        -D PYTHON2_EXECUTABLE=/usr/bin/python2.7 \
        -D PYTHON_INCLUDE_DIR=/usr/include/python2.7 \ 
        -D WITH_FFMPEG=ON \
        -D WITH_TBB=ON \
        -D WITH_IPP=OFF \
        -D CV_DISABLE_OPTIMIZATION=OFF \
        -D BUILD_SHARED_LIBS=OFF \
        -D BUILD_TESTS=OFF \
        -D BUILD_PERF_TESTS=OFF \
        -D BUILD_DOCS=OFF \
        .. \
 && make -j$(nproc) && make install && cd .. && rm -rf build \
 && ln -s /usr/local/python/cv2/python-2.7/cv2.so /usr/lib/python2.7/site-packages/cv2.so \
 && rm -rf /opt/opencv_contrib-4.0.0 \
 && rm -rf /opt/opencv-4.0.0

RUN apk add --update --no-cache hdf5@edgetest hdf5-dev@edgetest \
 && pip2 install --no-cache-dir -U pip \
 && pip2 install --no-cache-dir keras==2.2.4 \
 && pip2 install --no-cache-dir pathlib==1.0.1 \
 && pip2 install --no-cache-dir Cython==0.29.13 \
 && pip2 install --no-cache-dir scikit-image==0.14.3 \
 && pip2 install --no-cache-dir python-swiftclient==3.8.1 \
 && pip2 install --no-cache-dir python-keystoneclient==3.21.0 \
 && pip2 install --no-cache-dir redis==3.3.8 \
 && pip2 install --no-cache-dir cryptography==2.7

ADD app/ /app-raw/

FROM sconecuratedimages/issre2019:runtime-alpine3.7 as intermediate

COPY --from=base / rootvol/

RUN mkdir -p rootvol/app rootvol/input

RUN rm -rf rootvol/dev \
           rootvol/proc \
           rootvol/media \
           rootvol/mnt \
           rootvol/usr/share/X11 \
           rootvol/usr/share/terminfo \
           rootvol/usr/include/c++/ \
           rootvol/usr/lib/tcl8.6 \
           rootvol/usr/lib/gcc \
           rootvol/sys \
           rootvol/usr/include/c++

ENV SCONE_VERSION=1 \
    SCONE_HEAP=2G

# Create FSPF
RUN scone fspf create fspf.pb

# Add / region
RUN scone fspf addr fspf.pb / --kernel / --not-protected

# Add /app region & files - encrypted
RUN scone fspf addr fspf.pb /app --encrypted --kernel /app \
 && scone fspf addf fspf.pb /app rootvol/app-raw rootvol/app \
 && rm -rf rootvol/app-raw

# Add system folders to autheticated regions
RUN scone fspf addr fspf.pb /usr --kernel /usr --authenticated \
 && scone fspf addf fspf.pb /usr rootvol/usr /usr

RUN scone fspf addr fspf.pb /lib --kernel /lib --authenticated \
 && scone fspf addf fspf.pb /lib rootvol/lib /lib

# Add input directory as ephemeral
RUN scone fspf addr fspf.pb /input --encrypted --ephemeral

# trick to break the cache from here
ARG DATETIME=unknown
# Finally, encrypt FSPF file
RUN scone fspf encrypt fspf.pb

# Same target image with fspf file copied from intermediate
FROM sconecuratedimages/issre2019:runtime-alpine3.7

COPY --from=intermediate rootvol /
COPY --from=intermediate fspf.pb /
ADD scripts/export_env.sh /export_env.sh

WORKDIR /app
