# Maintainer: Bumsik Kim <k.bumsik@gmail.com>
_pkgname_camelcase=VirtScreen
pkgname=virtscreen
pkgver=0.1.1
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
sha256sums=('0207fa4c2d1ddebd35d42ce7489e8a357bf565b7e962073cdfd6521d56b92fc4')

build() {
  echo "$pkgdir"
  cd $_pkgname_camelcase-$pkgver
  python setup.py build
}

package() {
  cd $_pkgname_camelcase-$pkgver
  python setup.py install --root="$pkgdir/" --optimize=1 --skip-build
  install -Dm644 "$pkgname.desktop" "$pkgdir/usr/share/applications/$pkgname.desktop"
  install -Dm644 "$pkgname/icon/icon.png" "$pkgdir/usr/share/pixmaps/$pkgname.png"
}