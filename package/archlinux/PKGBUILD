# Maintainer: Bumsik Kim <k.bumsik@gmail.com>
_pkgname_camelcase=VirtScreen
pkgname=virtscreen
pkgver=0.1.3
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
sha256sums=('79cd7a07fc5eb9d6034812cca39612cb1cbef109bd2c8e939a45e2186a82cac2')

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