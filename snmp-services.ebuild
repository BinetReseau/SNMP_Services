# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=4

DESCRIPTION="Scripts to monitor the services of a server with SNMP."
HOMEPAGE="https://github.com/BinetReseau/SNMP_Services"
LICENSE="MIT-like"

if [[ ${PV} == *9999* ]]; then
	inherit git-2
	EGIT_REPO_URI="https://github.com/BinetReseau/SNMP_Services.git"
	SRC_URI=""
else
	inherit vcs-snapshot
	SRC_URI="https://github.com/BinetReseau/SNMP_Services/tarball/${PV} -> ${P}.tar.gz"
fi

SLOT="0"
KEYWORDS="~x86 ~amd64"
IUSE="nagios snmp"

DEPEND="nagios? ( dev-python/pysnmp )"
RDEPEND="${RDEPEND}"

src_install() {
	if use nagios ; then
		dodir /usr/lib/nagios/plugins/contrib
		exeinto /usr/lib/nagios/plugins/contrib
		doexe check_snmp_services.py
	fi

	if use snmp ; then
		dodir /usr/bin
		dobin snmp_gentoo_services.py
	fi
}

