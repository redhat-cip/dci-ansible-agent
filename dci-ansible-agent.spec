Name:           dci-ansible-agent
Version:        0.0.VERS
Release:        1%{?dist}
Summary:        DCI Ansible Agent for DCI control server
License:        ASL 2.0
URL:            https://github.com/redhat-openstack/dci-ansible-agent
BuildArch:      noarch
Source0:        dci-ansible-agent-%{version}.tar.gz

BuildRequires:  dci-ansible
BuildRequires:  ansible
BuildRequires:  systemd
BuildRequires:  systemd-units
Requires:       dci-ansible
Requires:       ansible

Requires(pre): shadow-utils
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
DCI Ansible Agent for DCI control server.

%prep
%setup -qc

%build

%install
install -p -D -m 644 systemd/%{name}.service %{buildroot}%{_unitdir}/%{name}.service
install -p -D -m 644 systemd/%{name}.timer %{buildroot}%{_unitdir}/%{name}.timer
install -p -D -m 644 systemd/dci-update.service %{buildroot}%{_unitdir}/dci-update.service
install -p -D -m 644 systemd/dci-update.timer %{buildroot}%{_unitdir}/dci-update.timer
install -p -D -m 644 ansible.cfg %{buildroot}%{_datadir}/dci-ansible-agent/ansible.cfg
install -p -D -m 644 dci-ansible-agent.yml %{buildroot}%{_datadir}/dci-ansible-agent/dci-ansible-agent.yml
install -p -D -m 644 dcirc.sh %{buildroot}%{_sysconfdir}/dci-ansible-agent/dcirc.sh
install -p -D -m 644 hooks/pre-run.yml %{buildroot}%{_sysconfdir}/dci-ansible-agent/hooks/pre-run.yml
install -p -D -m 644 hooks/running.yml %{buildroot}%{_sysconfdir}/dci-ansible-agent/hooks/running.yml
install -p -D -m 644 hooks/teardown.yml %{buildroot}%{_sysconfdir}/dci-ansible-agent/hooks/teardown.yml
install -p -D -m 644 settings.yml %{buildroot}%{_sysconfdir}/dci-ansible-agent/settings.yml
install -p -D -m 644 dci-ansible-agent.sudo %{buildroot}%{_sysconfdir}/sudoers.d/dci-ansible-agent
install -p -d -m 755 %{buildroot}/%{_sharedstatedir}/dci-ansible-agent

%clean

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
    useradd -r -m -g %{name} -d %{_sharedstatedir}/%{name} -s /sbin/nologin \
            -c "DCI-Agent service" %{name}
exit 0

%post
%systemd_post %{name}.service
%systemd_post dci-update.service
%systemd_post %{name}.timer
%systemd_post dci-update.timer

%preun
%systemd_preun %{name}.service
%systemd_preun dci-update.service
%systemd_preun %{name}.timer
%systemd_preun dci-update.timer

%postun
%systemd_postun

%files
%{_unitdir}/*
%{_datadir}/dci-ansible-agent
%config(noreplace) %{_sysconfdir}/dci-ansible-agent/dcirc.sh
%config(noreplace) %{_sysconfdir}/dci-ansible-agent/settings.yml
%config(noreplace) %{_sysconfdir}/dci-ansible-agent/hooks/pre-run.yml
%config(noreplace) %{_sysconfdir}/dci-ansible-agent/hooks/running.yml
%config(noreplace) %{_sysconfdir}/dci-ansible-agent/hooks/teardown.yml
%dir %{_sharedstatedir}/dci-ansible-agent
%attr(0755, %{name}, %{name}) %{_sharedstatedir}/dci-ansible-agent
/etc/sudoers.d/dci-ansible-agent

%changelog
* Tue Mar 28 2017 Gonéri Le Bouder <goneri@redhat.com> - 0.0.0-1
- Initial release
