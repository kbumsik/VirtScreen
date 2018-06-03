# Maintainer: Bumsik Kim <k.bumsik@gmail.com>
_pkgname_camelcase=VirtScreen
pkgname=virtscreen
pkgver=0.2.0
pkgrel=1
pkgdesc="Make your iPad/tablet/computer as a secondary monitor on Linux"
arch=("i686" "x86_64")
url="https://github.com/kbumsik/VirtScreen"
license=('GPL')
groups=()
depends=('xorg-xrandr' 'x11vnc' 'python-pyqt5' 'python-twisted' 'python-netifaces' 'python-qt5reactor')
makedepends=('python-setuptools')
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
source=(https://github.com/kbumsik/$_pkgname_camelcase/archive/$pkgver.tar.gz)
noextract=()
sha256sums=('73cb4016b06ccb7a18a7aefc5822119655f1c260915bc34218d3b04ac86af3d8')

build() {
  echo "$pkgdir"
  cd $_pkgname_camelcase-$pkgver
  /usr/bin/python3 setup.py build
}

package() {
  cd $_pkgname_camelcase-$pkgver
  /usr/bin/python3 setup.py install --root="$pkgdir/" --optimize=1 --skip-build
  # These are already installed by setup.py
  # install -Dm644 "data/$pkgname.desktop" "$pkgdir/usr/share/applications/$pkgname.desktop"
  # install -Dm644 "data/icon.png" "$pkgdir/usr/share/pixmaps/$pkgname.png"
}