# Copyright 2022 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)

%define script_dir /opt/cray/bican-utils
%define script_utils_dir /opt/cray/bican-utils/utils

Name: bican-utils
Vendor: Hewlett Packard Enterprise Company
License: HPE Proprietary 
Summary: Install of bican utils scripts
Version: %(cat .version) 
Release: %(echo ${BUILD_METADATA})
Source: %{name}-%{version}.tar.bz2

Requires: python3-pyroute2

%description
This RPM when installed will install various scripts for bican configuration

%files
%defattr(755, root, root)
%dir %{script_dir}
%dir %{script_utils_dir}
%{script_dir}/bi-can-default-route.py
%{script_dir}/bi-can-get-sls-toggle.py
%{script_dir}/bi-can-ssh.py
%{script_dir}/bi-can-interface.py
%{script_utils_dir}/network.py
%{script_utils_dir}/sls.py

%prep
%setup -q

%build

%install
install -m 755 -d %{buildroot}%{script_dir}/
install -m 755 -d %{buildroot}%{script_utils_dir}/
install -m 755 scripts/bi-can-default-route.py %{buildroot}%{script_dir}
install -m 755 scripts/bi-can-get-sls-toggle.py %{buildroot}%{script_dir}
install -m 755 scripts/bi-can-ssh.py %{buildroot}%{script_dir}
install -m 755 scripts/bi-can-interface.py %{buildroot}%{script_dir}
install -m 755 scripts/utils/network.py %{buildroot}%{script_utils_dir}
install -m 755 scripts/utils/sls.py %{buildroot}%{script_utils_dir}

exit 0
