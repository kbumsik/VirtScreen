# Maintainer: Bumsik Kim <k.bumsik@gmail.com>
_pkgname_camelcase=VirtScreen
pkgname=virtscreen
pkgver=0.3.1
pkgrel=1
pkgdesc="Make your iPad/tablet/computer as a secondary monitor on Linux"
arch=("i686" "x86_64")
url="https://github.com/kbumsik/VirtScreen"
license=('GPL')
groups=()
depends=('xorg-xrandr' 'x11vnc' 'python-pyqt5' 'qt5-quickcontrols2' 'python-quamash-git' 'python-netifaces')
makedepends=('python-pip' 'perl')
optdepends=(
    'arandr: for display settings option'
)
provides=($pkgname)
conflicts=()
replaces=()
backup=()
options=()
install=
changelog=
source=(src::git+https://github.com/kbumsik/$_pkgname_camelcase.git#tag=$pkgver)
noextract=()
md5sums=('SKIP')

prepare() {
  cd $srcdir/src
  # Delete PyQt5 from install_requires because python-pyqt5 does not have PyPI metadata.
	# See https://bugs.archlinux.org/task/58887
  perl -pi -e "s/\'PyQt5>=\d+\.\d+\.\d+\',//" \
			setup.py
}

package() {
  cd $srcdir/src
  PIP_CONFIG_FILE=/dev/null /usr/bin/pip install --isolated --root="$pkgdir" --ignore-installed --ignore-requires-python --no-deps .
  # These are already installed by setup.py
  # install -Dm644 "data/$pkgname.desktop" "$pkgdir/usr/share/applications/$pkgname.desktop"
  # install -Dm644 "data/icon.png" "$pkgdir/usr/share/pixmaps/$pkgname.png"
}