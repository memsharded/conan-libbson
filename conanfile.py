from conans import ConanFile, AutoToolsBuildEnvironment, CMake
from conans.tools import download, untargz, check_sha1, replace_in_file, environment_append
import os

class LibbsonConan(ConanFile):
    name = "libbson"
    version = "1.7.0"
    url = "https://github.com/theirix/conan-libbson"
    license = "https://github.com/mongodb/libbson/blob/master/COPYING"
    description = "A BSON utility library."
    FOLDER_NAME = 'libbson-%s' % version
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"

    def config_options(self):
        del self.settings.compiler.libcxx

    def source(self):
        tarball_name = self.FOLDER_NAME + '.tar.gz'
        download("https://github.com/mongodb/libbson/releases/download/%s/%s.tar.gz"
                 % (self.version, self.FOLDER_NAME), tarball_name)
        check_sha1(tarball_name, "5c8119a7500a9131e0a6b0c7357bbac4069ade56")
        untargz(tarball_name)
        os.unlink(tarball_name)

    def build(self):

        if self.settings.os == "Linux" or self.settings.os == "Macos":

            env_build = AutoToolsBuildEnvironment(self)

            # compose configure options
            suffix = ''
            if self.options.shared:
                suffix += " --enable-shared --disable-static"
            else:
                suffix += " --disable-shared --enable-static"

            with environment_append(env_build.vars):
                # refresh configure
                cmd = 'cd %s/%s && autoreconf --force --verbose --install -I build/autotools' % (self.conanfile_directory, self.FOLDER_NAME)
                self.run(cmd)

                # disable rpath build
                old_str = "-install_name \$rpath/"
                new_str = "-install_name "
                replace_in_file("%s/%s/configure" % (self.conanfile_directory, self.FOLDER_NAME), old_str, new_str)

                cmd = 'cd %s/%s && ./configure --prefix=%s/%s/_inst %s' % (self.conanfile_directory, self.FOLDER_NAME,
                                                                        self.conanfile_directory, self.FOLDER_NAME, suffix)
                self.output.warn('Running: ' + cmd)
                self.run(cmd)

                cmd = 'cd %s/%s && make install' % (self.conanfile_directory, self.FOLDER_NAME)
                self.output.warn('Running: ' + cmd)
                self.run(cmd)

        if self.settings.os == "Windows":
            cmake = CMake(self)
            if self.options.shared:
                cmake.definitions["ENABLED_STATIC"] = "OFF"
            else:
                cmake.definitions["ENABLED_STATIC"] = "ON"
            cmake.configure(source_dir=self.conanfile_directory, build_dir=("%s/_inst" % (self.FOLDER_NAME)))
            cmake.build()
            cmake.install()

    def package(self):
        os.rename("%s/COPYING" % (self.FOLDER_NAME), "%s/LICENSE" % (self.FOLDER_NAME))
        self.copy("license*", src="%s" % (self.FOLDER_NAME), dst="licenses", ignore_case=True, keep_path=False)
        self.copy(pattern="*.h", dst="include", src="%s/_inst/include" % (self.FOLDER_NAME), keep_path=True)
        if self.options.shared:
            if self.settings.os == "Macos":
                self.copy(pattern="*.dylib", src="%s/_inst/lib" % (self.FOLDER_NAME), dst="lib", keep_path=False)
            elif self.settings.os == "Windows":
                self.copy(pattern="*.dll*", src="%s/_inst/lib" % (self.FOLDER_NAME), dst="lib", keep_path=False)
            else:
                self.copy(pattern="*.so*", src="%s/_inst/lib" % (self.FOLDER_NAME), dst="lib", keep_path=False)
        else:
            self.copy(pattern="*bson*.a", src="%s/_inst/lib" % (self.FOLDER_NAME), dst="lib", keep_path=False)
        if self.settings.os == "Windows":
            self.copy(pattern="*.lib*", src="%s/_inst/lib" % (self.FOLDER_NAME), dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ['bson-1.0']
        self.cpp_info.includedirs = ['include/libbson-1.0']
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["pthread", "rt"])
