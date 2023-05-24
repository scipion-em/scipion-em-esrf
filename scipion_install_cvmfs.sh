export CUDA_VERSION=10.1
module load cuda/10.1
export SCIPION3_VERSION=$(date +%Y%m%d)_cuda$CUDA_VERSION
export SCIPION_INSTALL_DIR=/cvmfs/sb.esrf.fr/software/packages/ubuntu20.04/x86_64/scipion3/$SCIPION3_VERSION

if [ -d "$SCIPION_INSTALL_DIR" ]; then
  echo "Directory '$SCIPION_INSTALL_DIR' already exists!"
  echo "Please remove before proceeding with installation."
  exit 1
fi

mkdir -p $SCIPION_INSTALL_DIR
cd $SCIPION_INSTALL_DIR

# Create anaconda / miniconda installation in this directory:
~/Miniconda3-py39_4.9.2-Linux-x86_64.sh -b -p $SCIPION_INSTALL_DIR/miniconda3

eval "$($SCIPION_INSTALL_DIR/miniconda3/bin/conda shell.bash hook)"
export CONDA_ACTIVATION_CMD=". $SCIPION_INSTALL_DIR/miniconda3/etc/profile.d/conda.sh"

# Update conda:

conda update -n base conda -y
conda config --set channel_priority flexible

# Create scipion3 virtual environment:

conda create -n scipion_install python=3.9 -y
conda activate scipion_install

pip install scipion-installer
python3 -m scipioninstaller -conda -noXmipp -noAsk $SCIPION_INSTALL_DIR

# Configuration

$SCIPION_INSTALL_DIR/scipion3 config --overwrite --unattended

cp /opt/pxsoft/scipion/config/scipion.conf $SCIPION_INSTALL_DIR/config
cp /opt/pxsoft/scipion/config/hosts.conf $SCIPION_INSTALL_DIR/config

# Install boost (needed by TANGO)

$SCIPION_INSTALL_DIR/scipion3 run conda install boost=1.71.0 -y

# Install better fonts:

$SCIPION_INSTALL_DIR/scipion3 run conda remove tk --force -y
wget https://anaconda.org/scipion/tk/8.6.10/download/linux-64/tk-8.6.10-h14c3975_1005.tar.bz2
$SCIPION_INSTALL_DIR/scipion3 run conda install tk-8.6.10-h14c3975_1005.tar.bz2 -y

# Install plugins

$SCIPION_INSTALL_DIR/scipion3 installp -p scipion-em-xmipp -j 16 | tee -a install.log

# Re-iterate the previous command, it systematically fails the first time
sleep 5
$SCIPION_INSTALL_DIR/scipion3 installp -p scipion-em-xmipp -j 16 | tee -a install.log

# Give time to clear cache etc.
sleep 10

./scipion3 installp -p scipion-em-bsoft -j 16

./scipion3 installp -p scipion-em-cistem -j 16

$SCIPION_INSTALL_DIR/scipion3 installp -p scipion-em-relion -j 16 | tee -a install.log
# cd $SCIPION_INSTALL_DIR/software/em/relion-4.0
# mkdir build
# cd build
# cmake .. -DCMAKE_C_COMPILER=gcc-8 -DCMAKE_CXX_COMPILER=g++-8
# cd ..
# make -j 16
# cd $SCIPION_INSTALL_DIR

# ./scipion3 installb relion_python

./scipion3 installp -p scipion-em-eman2 -j 16

./scipion3 installp -p scipion-em-facilities

./scipion3 installp -p scipion-em-gautomatch

./scipion3 installp -p scipion-em-gctf

./scipion3 installp -p scipion-em-motioncorr
./scipion3 installb motioncor2-1.6.3

./scipion3 installp -p scipion-em-sphire
./scipion3 installb cryolo-1.9.3
./scipion3 installb cryoloCPU-1.9.3
./scipion3 installb cryolo_model-202005_N63_c17

./scipion3 installp -p scipion-em-topaz

./scipion3 installp -p scipion-em-tomo

./scipion3 installp -p scipion-em-aretomo

git clone git@github.com:scipion-em/scipion-em-esrf
./scipion3 installp -p ./scipion-em-esrf --devel


