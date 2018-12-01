#! /bin/bash
# Make a debian/ubuntu distribution

name=$1
vers=$2
url=http://github.com/jnweiger/inkscape-clean-path
requires="bash"

tmp=../out

[ -d $tmp ] && rm -rf $tmp/*.deb
mkdir $tmp
cd files
fakeroot checkinstall --fstrans --reset-uid --type debian \
  --install=no -y --pkgname $name --pkgversion $vers --arch all \
  --pkglicense LGPL --pkggroup other --pakdir ../$tmp --pkgsource $url \
  --pkgaltsource "http://github.com/jnweiger/inkscape-clean-path" \
  --maintainer "'Juergen Weigert (juergen@fabmail.org)'" \
  --requires "$requires" make install \
  -e PREFIX=/usr > /dev/null || { echo "error"; exit 1; }

cd ..; rm files/*
