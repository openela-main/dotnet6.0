# CentOS Koji doesn't understand %%bootstrap
%bcond_with bootstrap_dotnet

# Avoid provides/requires from private libraries
%global privlibs             libhostfxr
%global privlibs %{privlibs}|libclrjit
%global privlibs %{privlibs}|libcoreclr
%global privlibs %{privlibs}|libcoreclrtraceptprovider
%global privlibs %{privlibs}|libdbgshim
%global privlibs %{privlibs}|libhostpolicy
%global privlibs %{privlibs}|libmscordaccore
%global privlibs %{privlibs}|libmscordbi
%global privlibs %{privlibs}|libsos
%global privlibs %{privlibs}|libsosplugin
%global __provides_exclude ^(%{privlibs})\\.so
%global __requires_exclude ^(%{privlibs})\\.so

# LTO triggers a compilation error for a source level issue.  Given that LTO should not
# change the validity of any given source and the nature of the error (undefined enum), I
# suspect a generator program is mis-behaving in some way.  This needs further debugging,
# until that's done, disable LTO.  This has to happen before setting the flags below.
%define _lto_cflags %{nil}

%global host_version 6.0.32
%global runtime_version 6.0.32
%global aspnetcore_runtime_version %{runtime_version}
%global sdk_version 6.0.132
%global sdk_feature_band_version %(echo %{sdk_version} | sed -e 's|[[:digit:]][[:digit:]]$|00|')
%global templates_version %{runtime_version}
#%%global templates_version %%(echo %%{runtime_version} | awk 'BEGIN { FS="."; OFS="." } {print $1, $2, $3+1 }')

%global host_rpm_version %{host_version}
%global runtime_rpm_version %{runtime_version}
%global aspnetcore_runtime_rpm_version %{aspnetcore_runtime_version}
%global sdk_rpm_version %{sdk_version}

# upstream can update releases without revving the SDK version so these don't always match
%global upstream_tag v%{sdk_version}

%if 0%{?fedora} || 0%{?rhel} < 8
%global use_bundled_libunwind 0
%else
%global use_bundled_libunwind 1
%endif

%ifarch aarch64 s390x
%global use_bundled_libunwind 1
%endif

%ifarch x86_64
%global runtime_arch x64
%endif
%ifarch aarch64
%global runtime_arch arm64
%endif
%ifarch s390x
%global runtime_arch s390x
%endif

%{!?runtime_id:%global runtime_id %(. /etc/os-release ; echo "${ID}.${VERSION_ID%%.*}")-%{runtime_arch}}

Name:           dotnet6.0
Version:        %{sdk_rpm_version}
Release:        1%{?dist}
Summary:        .NET Runtime and SDK
License:        MIT and ASL 2.0 and BSD and LGPLv2+ and CC-BY and CC0 and MS-PL and EPL-1.0 and GPL+ and GPLv2 and ISC and OFL and zlib
URL:            https://github.com/dotnet/

%if %{with bootstrap_dotnet}
%global bootstrap_sdk_version 6.0.120
# The source is generated on a RHEL box via:
# ./build-dotnet-tarball --bootstrap %%{upstream_tag}
Source0:        dotnet-%{upstream_tag}-x64-bootstrap.tar.xz
# Generated via ./build-arm64-bootstrap-tarball
Source1:        dotnet-prebuilts-%{bootstrap_sdk_version}-arm64.tar.gz
# Generated manually, same pattern as the arm64 tarball
Source2:        dotnet-prebuilts-%{bootstrap_sdk_version}-s390x.tar.gz
%else
# The source is generated on a RHEL box via:
# ./build-dotnet-tarball %%{upstream_tag}
Source0:        dotnet-%{upstream_tag}.tar.gz
%endif


Source10:       check-debug-symbols.py
Source11:       dotnet.sh.in

# Fix using lld on RHEL
Patch100:       runtime-arm64-lld-fix.patch
# Mono still has a dependency on (now unbuildable) ILStrip which was removed from CoreCLR: https://github.com/dotnet/runtime/pull/60315
Patch101:       runtime-mono-remove-ilstrip.patch
# https://github.com/dotnet/runtime/pull/95217#issuecomment-1842799362
Patch102:       runtime-re-enable-implicit-rejection.patch

# Disable apphost, needed for s390x
Patch500:       fsharp-no-apphost.patch

# Disable apphost, needed for s390x
Patch700:       arcade-no-apphost.patch

# Named mutex fix for mono, needed for s390x. https://github.com/dotnet/roslyn/pull/57003
Patch800:       roslyn-57003-mono-named-mutex.patch
# Disable apphost, needed for s390x
Patch801:       roslyn-no-apphost.patch

# Disable apphost, needed for s390x
Patch900:       roslyn-analyzers-no-apphost.patch

# Fix mono-specific runtime crashes running msbuild. CoreCLR does not
# load types that are not actually used/invoked at runtime, while mono
# does. System.Configuration and System.Security are missing in
# source-build builds, which breaks msbuild.
Patch1000:      msbuild-no-systemsecurity.patch
Patch1001:      msbuild-no-systemconfiguration.patch

# Disable telemetry by default; make it opt-in
Patch1500:      sdk-telemetry-optout.patch


%if 0%{?fedora} || 0%{?rhel} >= 8
ExclusiveArch:  aarch64 x86_64 s390x
%else
ExclusiveArch:  x86_64
%endif

BuildRequires:  clang
BuildRequires:  cmake
BuildRequires:  coreutils
%if %{without bootstrap_dotnet}
BuildRequires:  dotnet-sdk-6.0
BuildRequires:  dotnet-sdk-6.0-source-built-artifacts
%endif
BuildRequires:  findutils
BuildRequires:  git
%if 0%{?fedora} || 0%{?rhel} > 7
BuildRequires:  glibc-langpack-en
%endif
BuildRequires:  hostname
BuildRequires:  krb5-devel
BuildRequires:  libicu-devel
%if ! %{use_bundled_libunwind}
BuildRequires:  libunwind-devel
%endif
%ifarch aarch64
BuildRequires:  lld
%endif
BuildRequires:  llvm
BuildRequires:  lttng-ust-devel
BuildRequires:  make
BuildRequires:  openssl-devel
BuildRequires:  python3
BuildRequires:  tar
BuildRequires:  util-linux
BuildRequires:  zlib-devel

%description
.NET is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, macOS and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.

.NET contains a runtime conforming to .NET Standards a set of
framework libraries, an SDK containing compilers and a 'dotnet'
application to drive everything.


%package -n dotnet

Version:        %{sdk_rpm_version}
Summary:        .NET CLI tools and runtime

Requires:       dotnet-sdk-6.0%{?_isa} >= %{sdk_rpm_version}-%{release}

%description -n dotnet
.NET is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, macOS and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.

.NET contains a runtime conforming to .NET Standards a set of
framework libraries, an SDK containing compilers and a 'dotnet'
application to drive everything.


%package -n dotnet-host

Version:        %{host_rpm_version}
Summary:        .NET command line launcher

%description -n dotnet-host
The .NET host is a command line program that runs a standalone
.NET application or launches the SDK.

.NET is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, Mac and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.


%package -n dotnet-hostfxr-6.0

Version:        %{host_rpm_version}
Summary:        .NET command line host resolver

# Theoretically any version of the host should work. But lets aim for the one
# provided by this package, or from a newer version of .NET
Requires:       dotnet-host%{?_isa} >= %{host_rpm_version}-%{release}

%description -n dotnet-hostfxr-6.0
The .NET host resolver contains the logic to resolve and select
the right version of the .NET SDK or runtime to use.

.NET is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, Mac and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.


%package -n dotnet-runtime-6.0

Version:        %{runtime_rpm_version}
Summary:        NET 6.0 runtime

Requires:       dotnet-hostfxr-6.0%{?_isa} >= %{host_rpm_version}-%{release}

# libicu is dlopen()ed
Requires:       libicu%{?_isa}

# See src/runtime/src/libraries/Native/AnyOS/brotli-version.txt
Provides: bundled(libbrotli) = 1.0.9
%if %{use_bundled_libunwind}
# See runtime/src/coreclr/pal/src/libunwind/libunwind-version.txt
Provides: bundled(libunwind) = 1.5.rc1.28.g9165d2a1
%endif

%description -n dotnet-runtime-6.0
The .NET runtime contains everything needed to run .NET applications.
It includes a high performance Virtual Machine as well as the framework
libraries used by .NET applications.

.NET is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, Mac and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.


%package -n aspnetcore-runtime-6.0

Version:        %{aspnetcore_runtime_rpm_version}
Summary:        ASP.NET Core 6.0 runtime

Requires:       dotnet-runtime-6.0%{?_isa} >= %{runtime_rpm_version}-%{release}

%description -n aspnetcore-runtime-6.0
The ASP.NET Core runtime contains everything needed to run .NET
web applications. It includes a high performance Virtual Machine as
well as the framework libraries used by .NET applications.

ASP.NET Core is a fast, lightweight and modular platform for creating
cross platform web applications that work on Linux, Mac and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.


%package -n dotnet-templates-6.0

Version:        %{sdk_rpm_version}
Summary:        .NET 6.0 templates

# Theoretically any version of the host should work. But lets aim for the one
# provided by this package, or from a newer version of .NET
Requires:       dotnet-host%{?_isa} >= %{host_rpm_version}-%{release}

%description -n dotnet-templates-6.0
This package contains templates used by the .NET SDK.

.NET is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, Mac and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.


%package -n dotnet-sdk-6.0

Version:        %{sdk_rpm_version}
Summary:        .NET 6.0 Software Development Kit

Provides:       bundled(js-jquery)

Requires:       dotnet-runtime-6.0%{?_isa} >= %{runtime_rpm_version}-%{release}
Requires:       aspnetcore-runtime-6.0%{?_isa} >= %{aspnetcore_runtime_rpm_version}-%{release}

Requires:       dotnet-apphost-pack-6.0%{?_isa} >= %{runtime_rpm_version}-%{release}
Requires:       dotnet-targeting-pack-6.0%{?_isa} >= %{runtime_rpm_version}-%{release}
Requires:       aspnetcore-targeting-pack-6.0%{?_isa} >= %{aspnetcore_runtime_rpm_version}-%{release}
Requires:       netstandard-targeting-pack-2.1%{?_isa} >= %{sdk_rpm_version}-%{release}

Requires:       dotnet-templates-6.0%{?_isa} >= %{sdk_rpm_version}-%{release}

%description -n dotnet-sdk-6.0
The .NET SDK is a collection of command line applications to
create, build, publish and run .NET applications.

.NET is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, Mac and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.


%global dotnet_targeting_pack() %{expand:
%package -n %{1}

Version:        %{2}
Summary:        Targeting Pack for %{3} %{4}

Requires:       dotnet-host%{?_isa}

%description -n %{1}
This package provides a targeting pack for %{3} %{4}
that allows developers to compile against and target %{3} %{4}
applications using the .NET SDK.

%files -n %{1}
%dir %{_libdir}/dotnet/packs
%{_libdir}/dotnet/packs/%{5}
}

%dotnet_targeting_pack dotnet-apphost-pack-6.0 %{runtime_rpm_version} Microsoft.NETCore.App 6.0 Microsoft.NETCore.App.Host.%{runtime_id}
%dotnet_targeting_pack dotnet-targeting-pack-6.0 %{runtime_rpm_version} Microsoft.NETCore.App 6.0 Microsoft.NETCore.App.Ref
%dotnet_targeting_pack aspnetcore-targeting-pack-6.0 %{aspnetcore_runtime_rpm_version} Microsoft.AspNetCore.App 6.0 Microsoft.AspNetCore.App.Ref
#%%dotnet_targeting_pack netstandard-targeting-pack-2.1 %%{sdk_rpm_version} NETStandard.Library 2.1 NETStandard.Library.Ref


%package -n dotnet-sdk-6.0-source-built-artifacts

Version:        %{sdk_rpm_version}
Summary:        Internal package for building .NET 6.0 Software Development Kit

%description -n dotnet-sdk-6.0-source-built-artifacts
The .NET source-built archive is a collection of packages needed
to build the .NET SDK itself.

These are not meant for general use.


%prep
%if %{without bootstrap_dotnet}
%setup -q -n dotnet-%{upstream_tag}
%else

%setup -q -T -b 0 -n dotnet-%{upstream_tag}-x64-bootstrap

%ifnarch x86_64

rm -rf .dotnet
%ifarch aarch64
tar -x --strip-components=1 -f %{SOURCE1} -C packages/prebuilt
%endif
%ifarch s390x
tar -x --strip-components=1 -f %{SOURCE2} -C packages/prebuilt
%endif
mkdir -p .dotnet
tar xf packages/prebuilt/dotnet-sdk*.tar.gz -C .dotnet/
rm packages/prebuilt/dotnet-sdk*.tar.gz
boot_sdk_version=$(ls -1 .dotnet/sdk/)
sed -i -E 's|"dotnet": "[^"]+"|"dotnet" : "'$boot_sdk_version'"|' global.json

%ifarch ppc64le s390x
ilasm_version=$(ls packages/prebuilt| grep -i ilasm | tr 'A-Z' 'a-z' | sed -E 's|runtime.linux-'%{runtime_arch}'.microsoft.netcore.ilasm.||' | sed -E 's|.nupkg$||')
echo $ilasm_version

mkdir -p packages-customized-local
pushd packages-customized-local
tar xf ../packages/archive/Private.SourceBuilt.Artifacts.*.tar.gz
sed -i -E 's|<MicrosoftNETCoreILAsmVersion>[^<]+</MicrosoftNETCoreILAsmVersion>|<MicrosoftNETCoreILAsmVersion>'$ilasm_version'</MicrosoftNETCoreILAsmVersion>|' PackageVersions.props
sed -i -E 's|<MicrosoftNETCoreILAsmPackageVersion>[^<]+</MicrosoftNETCoreILAsmPackageVersion>|<MicrosoftNETCoreILAsmPackageVersion>'$ilasm_version'</MicrosoftNETCoreILAsmPackageVersion>|' PackageVersions.props
sed -i -E 's|<MicrosoftNETCoreILDAsmVersion>[^<]+</MicrosoftNETCoreILDAsmVersion>|<MicrosoftNETCoreILDAsmVersion>'$ilasm_version'</MicrosoftNETCoreILDAsmVersion>|' PackageVersions.props
sed -i -E 's|<MicrosoftNETCoreILDAsmPackageVersion>[^<]+</MicrosoftNETCoreILDAsmPackageVersion>|<MicrosoftNETCoreILDAsmPackageVersion>'$ilasm_version'</MicrosoftNETCoreILDAsmPackageVersion>|' PackageVersions.props
tar czf ../packages/archive/Private.SourceBuilt.Artifacts.*.tar.gz *
popd

%endif

%endif

%endif

%if %{without bootstrap_dotnet}
# Remove all prebuilts
find -iname '*.dll' -type f -delete
find -iname '*.so' -type f -delete
find -iname '*.tar.gz' -type f -delete
find -iname '*.nupkg' -type f -delete
find -iname '*.zip' -type f -delete
rm -rf .dotnet/
rm -rf packages/source-built

mkdir -p packages/archive
ln -s %{_libdir}/dotnet/source-built-artifacts/Private.SourceBuilt.Artifacts.*.tar.gz packages/archive/
ln -s %{_libdir}/dotnet/reference-packages/Private.SourceBuild.ReferencePackages*.tar.gz packages/archive/
%endif

# Fix bad hardcoded path in build
sed -i 's|/usr/share/dotnet|%{_libdir}/dotnet|' src/runtime/src/native/corehost/hostmisc/pal.unix.cpp

pushd src/runtime
%patch100 -p1
%patch101 -p1
%patch102 -p1
popd

pushd src/fsharp
%patch500 -p1
popd

pushd src/arcade
%patch700 -p1
popd

pushd src/roslyn
%patch800 -p3
%patch801 -p1
popd

pushd src/roslyn-analyzers
%patch900 -p1
popd

pushd src/msbuild

# These are mono-specific fixes. Mono is only used on s390x. Restrict
# patch to s390x to avoid potential risk in other architectures.
%ifarch s390x
%patch1000 -p1
%patch1001 -p1
%endif

popd

pushd src/sdk
%patch1500 -p1
popd

pushd src/installer
popd


%if ! %{use_bundled_libunwind}
sed -i -E 's|( /p:BuildDebPackage=false)|\1 --cmakeargs -DCLR_CMAKE_USE_SYSTEM_LIBUNWIND=TRUE|' src/runtime/eng/SourceBuild.props
%endif

%build
cat /etc/os-release

%if %{without bootstrap_dotnet}
# We need to create a copy because we will mutate this
cp -a %{_libdir}/dotnet previously-built-dotnet
%endif

%if 0%{?fedora} > 32 || 0%{?rhel} > 8
# Setting this macro ensures that only clang supported options will be
# added to ldflags and cflags.
%global toolchain clang
%set_build_flags
%else
# Filter flags not supported by clang
%global dotnet_cflags %(echo %optflags | sed -re 's/-specs=[^ ]*//g')
%global dotnet_ldflags %(echo %{__global_ldflags} | sed -re 's/-specs=[^ ]*//g')
export CFLAGS="%{dotnet_cflags}"
export CXXFLAGS="%{dotnet_cflags}"
export LDFLAGS="%{dotnet_ldflags}"
%endif

# -fstack-clash-protection breaks CoreCLR
CFLAGS=$(echo $CFLAGS  | sed -e 's/-fstack-clash-protection//' )
CXXFLAGS=$(echo $CXXFLAGS  | sed -e 's/-fstack-clash-protection//' )

%ifarch aarch64
# -mbranch-protection=standard breaks unwinding in CoreCLR through libunwind
CFLAGS=$(echo $CFLAGS | sed -e 's/-mbranch-protection=standard //')
CXXFLAGS=$(echo $CXXFLAGS | sed -e 's/-mbranch-protection=standard //')
%endif

%ifarch s390x
# -march=z13 -mtune=z14 makes clang crash while compiling .NET
CFLAGS=$(echo $CFLAGS | sed -e 's/ -march=z13//')
CFLAGS=$(echo $CFLAGS | sed -e 's/ -mtune=z14//')
CXXFLAGS=$(echo $CXXFLAGS | sed -e 's/ -march=z13//')
CXXFLAGS=$(echo $CXXFLAGS | sed -e 's/ -mtune=z14//')
%endif

export EXTRA_CFLAGS="$CFLAGS"
export EXTRA_CXXFLAGS="$CXXFLAGS"
export EXTRA_LDFLAGS="$LDFLAGS"

VERBOSE=1 ./build.sh \
%if %{without bootstrap_dotnet}
    --with-sdk previously-built-dotnet \
%endif
    -- \

echo \
    /v:n \
    /p:SkipPortableRuntimeBuild=true \
    /p:LogVerbosity=n \
    /p:MinimalConsoleLogOutput=false \
    /p:ContinueOnPrebuiltBaselineError=true \


sed -e 's|[@]LIBDIR[@]|%{_libdir}|g' %{SOURCE11} > dotnet.sh


%install
install -dm 0755 %{buildroot}%{_libdir}/dotnet
ls artifacts/%{runtime_arch}/Release
tar xf artifacts/%{runtime_arch}/Release/dotnet-sdk-%{sdk_version}-%{runtime_id}.tar.gz -C %{buildroot}%{_libdir}/dotnet/

# See https://github.com/dotnet/source-build/issues/2579
find %{buildroot}%{_libdir}/dotnet/ -type f -iname testhost.x86 -delete
find %{buildroot}%{_libdir}/dotnet/ -type f -iname vstest.console -delete

# Install managed symbols
# Disabled until https://github.com/dotnet/source-build/issues/2623 is sorted out
# tar xf artifacts/%%{runtime_arch}/Release/runtime/dotnet-runtime-symbols-*%%{runtime_version}*.tar.gz \
#    -C %%{buildroot}/%%{_libdir}/dotnet/shared/Microsoft.NETCore.App/%%{runtime_version}/

# Fix executable permissions on files
find %{buildroot}%{_libdir}/dotnet/ -type f -name 'apphost' -exec chmod +x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name 'singlefilehost' -exec chmod +x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name 'lib*so' -exec chmod +x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.a' -exec chmod -x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.dll' -exec chmod -x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.h' -exec chmod 0644 {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.json' -exec chmod -x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.pdb' -exec chmod -x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.props' -exec chmod -x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.pubxml' -exec chmod -x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.targets' -exec chmod -x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.txt' -exec chmod -x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.xml' -exec chmod -x {} \;

# Provided by dotnet-host from another SRPM
#install -dm 0755 %%{buildroot}%%{_sysconfdir}/profile.d/
#install dotnet.sh %%{buildroot}%%{_sysconfdir}/profile.d/

# Provided by dotnet-host from another SRPM
#install -dm 0755 %%{buildroot}/%%{_datadir}/bash-completion/completions
# dynamic completion needs the file to be named the same as the base command
#install src/sdk/scripts/register-completions.bash %%{buildroot}/%%{_datadir}/bash-completion/completions/dotnet

# TODO: the zsh completion script needs to be ported to use #compdef
#install -dm 755 %%{buildroot}/%%{_datadir}/zsh/site-functions
#install src/cli/scripts/register-completions.zsh %%{buildroot}/%%{_datadir}/zsh/site-functions/_dotnet

# Provided by dotnet-host from another SRPM
#install -dm 0755 %%{buildroot}%%{_bindir}
#ln -s ../../%%{_libdir}/dotnet/dotnet %%{buildroot}%%{_bindir}/

# Provided by dotnet-host from another SRPM
#install -dm 0755 %%{buildroot}%%{_mandir}/man1/
#find -iname 'dotnet*.1' -type f -exec cp {} %%{buildroot}%%{_mandir}/man1/ \;

# Provided by dotnet-host from another SRPM
#install -dm 0755 %%{buildroot}%%{_sysconfdir}/dotnet
#echo "%%{_libdir}/dotnet" >> install_location
#install install_location %%{buildroot}%%{_sysconfdir}/dotnet/
#echo "%%{_libdir}/dotnet" >> install_location_%%{runtime_arch}
#install install_location_%%{runtime_arch} %%{buildroot}%%{_sysconfdir}/dotnet/

install -dm 0755 %{buildroot}%{_libdir}/dotnet/source-built-artifacts
install -m 0644 artifacts/%{runtime_arch}/Release/Private.SourceBuilt.Artifacts.*.tar.gz %{buildroot}/%{_libdir}/dotnet/source-built-artifacts/


# Quick and dirty check for https://github.com/dotnet/source-build/issues/2731
test -f %{buildroot}%{_libdir}/dotnet/sdk/%{sdk_version}/Sdks/Microsoft.NET.Sdk/Sdk/Sdk.props

# Check debug symbols in all elf objects. This is not in %%check
# because native binaries are stripped by rpm-build after %%install.
# So we need to do this check earlier.
echo "Testing build results for debug symbols..."
%{SOURCE10} -v %{buildroot}%{_libdir}/dotnet/


# Self-check
%{buildroot}%{_libdir}/dotnet/dotnet --info
%{buildroot}%{_libdir}/dotnet/dotnet --version

# Provided by dotnet-host from another SRPM
rm %{buildroot}%{_libdir}/dotnet/LICENSE.txt
rm %{buildroot}%{_libdir}/dotnet/ThirdPartyNotices.txt
rm %{buildroot}%{_libdir}/dotnet/dotnet

# Provided by netstandard-targeting-pack-2.1 from another SRPM
rm -rf %{buildroot}%{_libdir}/dotnet/packs/NETStandard.Library.Ref/2.1.0


%files -n dotnet-hostfxr-6.0
%dir %{_libdir}/dotnet/host/fxr
%{_libdir}/dotnet/host/fxr/%{host_version}

%files -n dotnet-runtime-6.0
%dir %{_libdir}/dotnet/shared
%dir %{_libdir}/dotnet/shared/Microsoft.NETCore.App
%{_libdir}/dotnet/shared/Microsoft.NETCore.App/%{runtime_version}

%files -n aspnetcore-runtime-6.0
%dir %{_libdir}/dotnet/shared
%dir %{_libdir}/dotnet/shared/Microsoft.AspNetCore.App
%{_libdir}/dotnet/shared/Microsoft.AspNetCore.App/%{aspnetcore_runtime_version}

%files -n dotnet-templates-6.0
%dir %{_libdir}/dotnet/templates
%{_libdir}/dotnet/templates/%{templates_version}

%files -n dotnet-sdk-6.0
%dir %{_libdir}/dotnet/sdk
%{_libdir}/dotnet/sdk/%{sdk_version}
%dir %{_libdir}/dotnet/sdk-manifests
%{_libdir}/dotnet/sdk-manifests/%{sdk_feature_band_version}
%{_libdir}/dotnet/metadata
%dir %{_libdir}/dotnet/packs

%files -n dotnet-sdk-6.0-source-built-artifacts
%dir %{_libdir}/dotnet
%{_libdir}/dotnet/source-built-artifacts


%changelog
* Thu Jun 27 2024 Omair Majid <omajid@redhat.com> - 6.0.132-1
- Update to .NET SDK 6.0.132 and Runtime 6.0.32
- Resolves: RHEL-45319

* Tue Apr 09 2024 Omair Majid <omajid@redhat.com> - 6.0.129-2
- Update to .NET SDK 6.0.129 and Runtime 6.0.29
- Resolves: RHEL-31194

* Tue Mar 19 2024 Omair Majid <omajid@redhat.com> - 6.0.128-2
- Update to .NET SDK 6.0.128 and Runtime 6.0.28
- Resolves: RHEL-27539

* Wed Feb 14 2024 Omair Majid <omajid@redhat.com> - 6.0.127-2
- Update to .NET SDK 6.0.127 and Runtime 6.0.27
- Resolves: RHEL-23784

* Mon Jan 15 2024 Omair Majid <omajid@redhat.com> - 6.0.126-2
- Update to .NET SDK 6.0.126 and Runtime 6.0.26
- Resolves: RHEL-19798

* Mon Dec 11 2023 Omair Majid <omajid@redhat.com> - 6.0.125-2
- Update to .NET SDK 6.0.125 and Runtime 6.0.25
- Resolves: RHEL-15348

* Tue Oct 24 2023 Omair Majid <omajid@redhat.com> - 6.0.124-2
- Update to .NET SDK 6.0.124 and Runtime 6.0.24
- Resolves: RHEL-14466

* Mon Oct 16 2023 Omair Majid <omajid@redhat.com> - 6.0.123-2
- Update to .NET SDK 6.0.123 and Runtime 6.0.23
- Resolves: RHEL-11696

* Tue Sep 12 2023 Omair Majid <omajid@redhat.com> - 6.0.122-2
- Update to .NET SDK 6.0.122 and Runtime 6.0.22
- Resolves: RHEL-1996

* Thu Aug 24 2023 Omair Majid <omajid@redhat.com> - 6.0.121-4
- Disable bootstrap
- Related: RHBZ#2228566

* Wed Aug 23 2023 Omair Majid <omajid@redhat.com> - 6.0.121-3
- Rebootstrap
- Related: RHBZ#2228566

* Wed Aug 09 2023 Omair Majid <omajid@redhat.com> - 6.0.121-2
- Update to .NET SDK 6.0.121 and Runtime 6.0.21
- Resolves: RHBZ#2228566

* Tue Jul 11 2023 Omair Majid <omajid@redhat.com> - 6.0.120-2
- Update to .NET SDK 6.0.120 and Runtime 6.0.20
- Resolves: RHBZ#2219636

* Thu Jul 06 2023 Omair Majid <omajid@redhat.com> - 6.0.119-2
- Update to .NET SDK 6.0.119 and Runtime 6.0.19
- Resolves: RHBZ#2216218

* Thu Feb 16 2023 Omair Majid <omajid@redhat.com> - 6.0.114-2
- Update to .NET SDK 6.0.114 and Runtime 6.0.14
- Resolves: RHBZ#2166765

* Wed Jan 11 2023 Omair Majid <omajid@redhat.com> - 6.0.113-2
- Update to .NET SDK 6.0.113 and Runtime 6.0.13
- Resolves: RHBZ#2154456

* Wed Dec 14 2022 Omair Majid <omajid@redhat.com> - 6.0.112-2
- Update to .NET SDK 6.0.112 and Runtime 6.0.12
- Resolves: RHBZ#2150145

* Fri Nov 18 2022 Omair Majid <omajid@redhat.com> - 6.0.111-3
- Disable subpackages provided by another SRPM
- Related: RHBZ#2138275

* Wed Nov 16 2022 Omair Majid <omajid@redhat.com> - 6.0.111-2
- Update to .NET SDK 6.0.111 and Runtime 6.0.11
- Resolves: RHBZ#2138275

* Tue Aug 09 2022 Omair Majid <omajid@redhat.com> - 6.0.108-1
- Update to .NET SDK 6.0.108 and Runtime 6.0.8
- Resolves: RHBZ#2112408

* Thu Jul 21 2022 Omair Majid <omajid@redhat.com> - 6.0.107-2
- Update to .NET SDK 6.0.107 and Runtime 6.0.7
- Resolves: RHBZ#2103268

* Thu Jun 23 2022 Omair Majid <omajid@redhat.com> - 6.0.106-1
- Update to .NET SDK 6.0.106 and Runtime 6.0.6
- Resolves: RHBZ#2093430

* Mon May 16 2022 Omair Majid <omajid@redhat.com> - 6.0.105-1
- Update to .NET SDK 6.0.105 and Runtime 6.0.5
- Resolves: RHBZ#2082265

* Mon Apr 25 2022 Omair Majid <omajid@redhat.com> - 6.0.104-3
- Update to .NET SDK 6.0.104 and Runtime 6.0.4
- Resolves: RHBZ#2072006

* Thu Feb 17 2022 Omair Majid <omajid@redhat.com> - 6.0.102-1
- Update to .NET SDK 6.0.102 and Runtime 6.0.2
- Resolves: RHBZ#2030390
- Resolves: RHBZ#2048256

* Fri Dec 10 2021 Omair Majid <omajid@redhat.com> - 6.0.100-1
- Fix build against clang 13
- Resolves: RHBZ#2003061
- Resolves: RHBZ#2015536
- Resolves: RHBZ#2014666

* Sun Oct 31 2021 Omair Majid <omajid@redhat.com> - 6.0.100-0.10
- Disable bootstrap
- Related: RHBZ#2016373

* Sat Oct 30 2021 Omair Majid <omajid@redhat.com> - 6.0.100-0.9
- Fix msbuild to run on s390x
- Related: RHBZ#2016373

* Thu Oct 28 2021 Omair Majid <omajid@redhat.com> - 6.0.100-0.8
- Update to .NET SDK 6.0.100 and Runtime 6.0.0
- Related: RHBZ#2016373

* Wed Oct 27 2021 Adam Kimball <akimball@redhat.com> - 6.0.0-0.7.rc2
- Update to .NET SDK 6.0.100-rc.2 and Runtime 6.0.0-rc.2
- Resolves: RHBZ#2016373
 
* Fri Oct 08 2021 Omair Majid <omajid@redhat.com> - 6.0.0-0.6.28be3e9a006d90d8c6e87d4353b77882829df718
- Enable building on arm64
- Related: RHBZ#1986017

* Sun Oct 03 2021 Omair Majid <omajid@redhat.com> - 6.0.0-0.5.28be3e9a006d90d8c6e87d4353b77882829df718
- Enable building on s390x
- Related: RHBZ#1986017

* Sun Oct 03 2021 Omair Majid <omajid@redhat.com> - 6.0.0-0.4.28be3e9a006d90d8c6e87d4353b77882829df718
- Clean up tarball and add initial support for s390x
- Related: RHBZ#1986017

* Sun Sep 26 2021 Omair Majid <omajid@redhat.com> - 6.0.0-0.3.28be3e9a006d90d8c6e87d4353b77882829df718
- Update to work-in-progress RC2 release

* Wed Aug 25 2021 Omair Majid <omajid@redhat.com> - 6.0.0-0.2.preview6
- Updated to build the latest source-build preview

* Fri Jul 23 2021 Omair Majid <omajid@redhat.com> - 6.0.0-0.1.preview6
- Initial package for .NET 6

* Thu Jun 10 2021 Omair Majid <omajid@redhat.com> - 5.0.204-1
- Update to .NET SDK 5.0.204 and Runtime 5.0.7

* Wed May 12 2021 Omair Majid <omajid@redhat.com> - 5.0.203-1
- Update to .NET SDK 5.0.203 and Runtime 5.0.6

* Wed Apr 14 2021 Omair Majid <omajid@redhat.com> - 5.0.202-1
- Update to .NET SDK 5.0.202 and Runtime 5.0.5

* Tue Apr 06 2021 Omair Majid <omajid@redhat.com> - 5.0.104-2
- Mark files under /etc/ as config(noreplace)
- Add an rpm-inspect configuration file
- Add an rpmlintrc file
- Enable gating for release branches and ELN too

* Tue Mar 16 2021 Omair Majid <omajid@redhat.com> - 5.0.104-1
- Update to .NET SDK 5.0.104 and Runtime 5.0.4
- Drop unneeded/upstreamed patches

* Wed Feb 17 2021 Omair Majid <omajid@redhat.com> - 5.0.103-2
- Add Fedora 35 RIDs

* Thu Feb 11 2021 Omair Majid <omajid@redhat.com> - 5.0.103-1
- Update to .NET SDK 5.0.103 and Runtime 5.0.3

* Fri Jan 29 2021 Omair Majid <omajid@redhat.com> - 5.0.102-2
- Disable bootstrap

* Fri Dec 18 2020 Omair Majid <omajid@redhat.com> - 5.0.100-2
- Update to .NET Core Runtime 5.0.0 and SDK 5.0.100 commit 9c4e5de

* Fri Dec 04 2020 Omair Majid <omajid@redhat.com> - 5.0.100-1
- Update to .NET Core Runtime 5.0.0 and SDK 5.0.100

* Thu Dec 03 2020 Omair Majid <omajid@redhat.com> - 5.0.100-0.4.20201202git337413b
- Update to latest 5.0 pre-GA commit

* Tue Nov 24 2020 Omair Majid <omajid@redhat.com> - 5.0.100-0.4.20201123gitdee899c
- Update to 5.0 pre-GA commit

* Mon Sep 14 2020 Omair Majid <omajid@redhat.com> - 5.0.100-0.3.preview8
- Update to Preview 8

* Fri Jul 10 2020 Omair Majid <omajid@redhat.com> - 5.0.100-0.2.preview4
- Fix building with custom CFLAGS/CXXFLAGS/LDFLAGS
- Clean up patches

* Mon Jul 06 2020 Omair Majid <omajid@redhat.com> - 5.0.100-0.1.preview4
- Initial build

* Sat Jun 27 2020 Omair Majid <omajid@redhat.com> - 3.1.105-4
- Disable bootstrap

* Fri Jun 26 2020 Omair Majid <omajid@redhat.com> - 3.1.105-3
- Re-bootstrap aarch64

* Fri Jun 19 2020 Omair Majid <omajid@redhat.com> - 3.1.105-3
- Disable bootstrap

* Thu Jun 18 2020 Omair Majid <omajid@redhat.com> - 3.1.105-1
- Bootstrap aarch64

* Tue Jun 16 2020 Chris Rummel <crummel@microsoft.com> - 3.1.105-1
- Update to .NET Core Runtime 3.1.5 and SDK 3.1.105

* Fri Jun 05 2020 Chris Rummel <crummel@microsoft.com> - 3.1.104-1
- Update to .NET Core Runtime 3.1.4 and SDK 3.1.104

* Thu Apr 09 2020 Chris Rummel <crummel@microsoft.com> - 3.1.103-1
- Update to .NET Core Runtime 3.1.3 and SDK 3.1.103

* Mon Mar 16 2020 Omair Majid <omajid@redhat.com> - 3.1.102-1
- Update to .NET Core Runtime 3.1.2 and SDK 3.1.102

* Fri Feb 28 2020 Omair Majid <omajid@redhat.com> - 3.1.101-4
- Disable bootstrap

* Fri Feb 28 2020 Omair Majid <omajid@redhat.com> - 3.1.101-3
- Enable bootstrap
- Add Fedora 33 runtime ids

* Thu Feb 27 2020 Omair Majid <omajid@redhat.com> - 3.1.101-2
- Disable bootstrap

* Tue Jan 21 2020 Omair Majid <omajid@redhat.com> - 3.1.101-1
- Update to .NET Core Runtime 3.1.1 and SDK 3.1.101

* Thu Dec 05 2019 Omair Majid <omajid@redhat.com> - 3.1.100-1
- Update to .NET Core Runtime 3.1.0 and SDK 3.1.100

* Mon Nov 18 2019 Omair Majid <omajid@redhat.com> - 3.1.100-0.4.preview3
- Fix apphost permissions

* Fri Nov 15 2019 Omair Majid <omajid@redhat.com> - 3.1.100-0.3.preview3
- Update to .NET Core Runtime 3.1.0-preview3.19553.2 and SDK
  3.1.100-preview3-014645

* Wed Nov 06 2019 Omair Majid <omajid@redhat.com> - 3.1.100-0.2
- Update to .NET Core 3.1 Preview 2

* Wed Oct 30 2019 Omair Majid <omajid@redhat.com> - 3.1.100-0.1
- Update to .NET Core 3.1 Preview 1

* Thu Oct 24 2019 Omair Majid <omajid@redhat.com> - 3.0.100-5
- Add cgroupv2 support to .NET Core

* Wed Oct 16 2019 Omair Majid <omajid@redhat.com> - 3.0.100-4
- Include fix from coreclr for building on Fedora 32

* Wed Oct 16 2019 Omair Majid <omajid@redhat.com> - 3.0.100-3
- Harden built binaries to pass annocheck

* Fri Oct 11 2019 Omair Majid <omajid@redhat.com> - 3.0.100-2
- Export DOTNET_ROOT in profile to make apphost lookup work

* Fri Sep 27 2019 Omair Majid <omajid@redhat.com> - 3.0.100-1
- Update to .NET Core Runtime 3.0.0 and SDK 3.0.100

* Wed Sep 25 2019 Omair Majid <omajid@redhat.com> - 3.0.100-0.18.rc1
- Update to .NET Core Runtime 3.0.0-rc1-19456-20 and SDK 3.0.100-rc1-014190

* Tue Sep 17 2019 Omair Majid <omajid@redhat.com> - 3.0.100-0.16.preview9
- Fix files duplicated between dotnet-apphost-pack-3.0 and dotnet-targeting-pack-3.0
- Fix dependencies between .NET SDK and the targeting packs

* Mon Sep 16 2019 Omair Majid <omajid@redhat.com> - 3.0.100-0.15.preview9
- Update to .NET Core Runtime 3.0.0-preview 9 and SDK 3.0.100-preview9

* Mon Aug 19 2019 Omair Majid <omajid@redhat.com> - 3.0.100-0.11.preview8
- Update to .NET Core Runtime 3.0.0-preview8-28405-07 and SDK
  3.0.100-preview8-013656

* Tue Jul 30 2019 Omair Majid <omajid@redhat.com> - 3.0.100-0.9.preview7
- Update to .NET Core Runtime 3.0.0-preview7-27912-14 and SDK
  3.0.100-preview7-012821

* Fri Jul 26 2019 Omair Majid <omajid@redhat.com> - 3.0.100-0.8.preview7
- Update to .NET Core Runtime 3.0.0-preview7-27902-19 and SDK
  3.0.100-preview7-012802

* Wed Jun 26 2019 Omair Majid <omajid@redhat.com> - 3.0.0-0.7.preview6
- Obsolete dotnet-sdk-3.0.1xx
- Add supackages for targeting packs
- Add -fcf-protection to CFLAGS

* Wed Jun 26 2019 Omair Majid <omajid@redhat.com> - 3.0.0-0.6.preview6
- Update to .NET Core Runtime 3.0.0-preview6-27804-01 and SDK 3.0.100-preview6-012264
- Set dotnet installation location in /etc/dotnet/install_location
- Update targeting packs
- Install managed symbols
- Completely conditionalize libunwind bundling

* Tue May 07 2019 Omair Majid <omajid@redhat.com> - 3.0.0-0.3.preview4
- Update to .NET Core 3.0 preview 4

* Tue Dec 18 2018 Omair Majid <omajid@redhat.com> - 3.0.0-0.1.preview1
- Update to .NET Core 3.0 preview 1

* Fri Dec 07 2018 Omair Majid <omajid@redhat.com> - 2.2.100
- Update to .NET Core 2.2.0

* Wed Nov 07 2018 Omair Majid <omajid@redhat.com> - 2.2.100-0.2.preview3
- Update to .NET Core 2.2.0-preview3

* Fri Nov 02 2018 Omair Majid <omajid@redhat.com> - 2.1.403-3
- Add host-fxr-2.1 subpackage

* Mon Oct 15 2018 Omair Majid <omajid@redhat.com> - 2.1.403-2
- Disable telemetry by default
- Users have to manually export DOTNET_CLI_TELEMETRY_OPTOUT=0 to enable

* Tue Oct 02 2018 Omair Majid <omajid@redhat.com> - 2.1.403-1
- Update to .NET Core Runtime 2.1.5 and SDK 2.1.403

* Wed Sep 26 2018 Omair Majid <omajid@redhat.com> - 2.1.402-2
- Add ~/.dotnet/tools to $PATH to make it easier to use dotnet tools

* Thu Sep 13 2018 Omair Majid <omajid@redhat.com> - 2.1.402-1
- Update to .NET Core Runtime 2.1.4 and SDK 2.1.402

* Wed Sep 05 2018 Omair Majid <omajid@redhat.com> - 2.1.401-2
- Use distro-standard flags when building .NET Core

* Tue Aug 21 2018 Omair Majid <omajid@redhat.com> - 2.1.401-1
- Update to .NET Core Runtime 2.1.3 and SDK 2.1.401

* Mon Aug 20 2018 Omair Majid <omajid@redhat.com> - 2.1.302-1
- Update to .NET Core Runtime 2.1.2 and SDK 2.1.302

* Fri Jul 20 2018 Omair Majid <omajid@redhat.com> - 2.1.301-1
- Update to .NET Core 2.1

* Thu May 03 2018 Omair Majid <omajid@redhat.com> - 2.0.7-1
- Update to .NET Core 2.0.7

* Wed Mar 28 2018 Omair Majid <omajid@redhat.com> - 2.0.6-2
- Enable bash completion for dotnet
- Remove redundant buildrequires and requires

* Wed Mar 14 2018 Omair Majid <omajid@redhat.com> - 2.0.6-1
- Update to .NET Core 2.0.6

* Fri Feb 23 2018 Omair Majid <omajid@redhat.com> - 2.0.5-1
- Update to .NET Core 2.0.5

* Wed Jan 24 2018 Omair Majid <omajid@redhat.com> - 2.0.3-5
- Don't apply corefx clang warnings fix on clang < 5

* Fri Jan 19 2018 Omair Majid <omajid@redhat.com> - 2.0.3-4
- Add a test script to sanity check debug and symbol info.
- Build with clang 5.0
- Make main package real instead of using a virtual provides (see RHBZ 1519325)

* Wed Nov 29 2017 Omair Majid <omajid@redhat.com> - 2.0.3-3
- Add a Provides for 'dotnet'
- Fix conditional macro

* Tue Nov 28 2017 Omair Majid <omajid@redhat.com> - 2.0.3-2
- Fix build on Fedora 27

* Fri Nov 17 2017 Omair Majid <omajid@redhat.com> - 2.0.3-1
- Update to .NET Core 2.0.3

* Thu Oct 19 2017 Omair Majid <omajid@redhat.com> - 2.0.0-4
- Add a hack to let omnisharp work

* Wed Aug 30 2017 Omair Majid <omajid@redhat.com> - 2.0.0-3
- Add a patch for building coreclr and core-setup correctly on Fedora >= 27

* Fri Aug 25 2017 Omair Majid <omajid@redhat.com> - 2.0.0-2
- Move libicu/libcurl/libunwind requires to runtime package
- Make sdk depend on the exact version of the runtime package

* Thu Aug 24 2017 Omair Majid <omajid@redhat.com> - 2.0.0-1
- Update to 2.0.0 final release

* Wed Jul 26 2017 Omair Majid <omajid@redhat.com> - 2.0.0-0.3.preview2
- Add man pages

* Tue Jul 25 2017 Omair Majid <omajid@redhat.com> - 2.0.0-0.2.preview2
- Add Requires on libicu
- Split into multiple packages
- Do not repeat first-run message

* Fri Jul 21 2017 Omair Majid <omajid@redhat.com> - 2.0.0-0.1.preview2
- Update to .NET Core 2.0 Preview 2

* Thu Mar 16 2017 Nemanja Milošević <nmilosevnm@gmail.com> - 1.1.0-7
- rebuilt with latest libldb
* Wed Feb 22 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-6
- compat-openssl 1.0 for F26 for now
* Sun Feb 19 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-5
- Fix wrong commit id's
* Sat Feb 18 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-4
- Use commit id's instead of branch names
* Sat Feb 18 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-3
- Improper patch5 fix
* Sat Feb 18 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-2
- SPEC cleanup
- git removal (using all tarballs for reproducible builds)
- more reasonable versioning
* Thu Feb 09 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-1
- Fixed debuginfo going to separate package (Patch1)
- Added F25/F26 RIL and fixed the version info (Patch2)
- Added F25/F26 RIL in Microsoft.NETCore.App suported runtime graph (Patch3)
- SPEC file cleanup
* Wed Jan 11 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-0
- Initial RPM for Fedora 25/26.
