Name:       ansible-role-openstack-stackdump
Version:    0.0.VERS
Release:    1%{?dist}
Summary:    ansible-role-openstack-stackdump
License:    ASL 2.0
URL:        https://github.com/redhat-cip/ansible-role-openstack-stackdump
Source0:    ansible-role-openstack-stackdump-%{version}.tar.gz

BuildArch:  noarch
Requires:   ansible

%description
An Ansible role to run and gather result from tripleo-stack-dump

%prep
%setup -qc


%build

%install
mkdir -p %{buildroot}%{_datadir}/dci/roles/openstack-stackdump
chmod 755 %{buildroot}%{_datadir}/dci/roles/openstack-stackdump

cp -r meta %{buildroot}%{_datadir}/dci/roles/openstack-stackdump
cp -r tasks %{buildroot}%{_datadir}/dci/roles/openstack-stackdump
cp -r defaults %{buildroot}%{_datadir}/dci/roles/openstack-stackdump


%files
%doc README.md
%license LICENSE
%{_datadir}/dci/roles/openstack-stackdump


%changelog
* Wed Apr 26 2017 Yanis Guenane <yguenane@redhat.com> - 0.0.1-1
- Initial release
