# Maintainer: Bumsik Kim <k.bumsik@gmail.com>
_pkgname_camelcase=VirtScreen
pkgname=virtscreen
pkgver=0.2.4
pkgrel=1
pkgdesc="Make your iPad/tablet/computer as a secondary monitor on Linux"
arch=("i686" "x86_64")
url="https://github.com/kbumsik/VirtScreen"
license=('GPL')
groups=()
depends=('xorg-xrandr' 'x11vnc' 'python-pyqt5' 'python-twisted' 'python-netifaces' 'python-qt5reactor')
makedepends=('python-pip')
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
sha256sums=('0a62fd5e2b89ff7d83f9769d33b6a795c452a8bf09cf2e61ccd8282b40cefd6f')

package() {
  cd $_pkgname_camelcase-$pkgver
  PIP_CONFIG_FILE=/dev/null /usr/bin/pip install --isolated --root="$pkgdir" --ignore-installed --no-deps .
  # These are already installed by setup.py
  # install -Dm644 "data/$pkgname.desktop" "$pkgdir/usr/share/applications/$pkgname.desktop"
  # install -Dm644 "data/icon.png" "$pkgdir/usr/share/pixmaps/$pkgname.png"
}