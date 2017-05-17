from conans import ConanFile, AutoToolsBuildEnvironment
from conans.tools import download, untargz, check_sha1, replace_in_file, environment_append
import os

class LibbsonConan(ConanFile):
    name = "libbson"
    version = "1.6.2"
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
        check_sha1(tarball_name, "67e5e290eded1f9d130b476964bc99b5fc15dfb2")
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

                cmd = 'cd %s/%s && ./configure %s' % (self.conanfile_directory, self.FOLDER_NAME, suffix)
                self.output.warn('Running: ' + cmd)
                self.run(cmd)

                cmd = 'cd %s/%s && make' % (self.conanfile_directory, self.FOLDER_NAME)
                self.output.warn('Running: ' + cmd)
                self.run(cmd)

    def package(self):
        # exclude private headers
        for header in ['atomic', 'clock', 'compat', 'config', 'context', 'endian', 'error', 'iter', 'json',\
                       'keys', 'macros', 'md5', 'memory', 'oid', 'reader', 'stdint', 'string', 'types', 'utf8',\
                       'value', 'version-functions', 'version', 'writer', 'decimal128']:
            self.copy('bson-'+header+'.h', dst="include/libbson-1.0", src="%s/src/bson" % (self.FOLDER_NAME), keep_path=False)
        self.copy("bcon.h", dst="include/libbson-1.0", src="%s/src/bson" % (self.FOLDER_NAME), keep_path=False)
        self.copy("bson.h", dst="include/libbson-1.0", src="%s/src/bson" % (self.FOLDER_NAME), keep_path=False)
        if self.options.shared:
            if self.settings.os == "Macos":
                self.copy(pattern="*.dylib", dst="lib", keep_path=False)
            else:
                self.copy(pattern="*.so*", dst="lib", keep_path=False)
        else:
            self.copy(pattern="*bson*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ['bson-1.0']
        self.cpp_info.includedirs = ['include/libbson-1.0']
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["pthread", "rt"])
