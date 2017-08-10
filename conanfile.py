from conans import ConanFile, AutoToolsBuildEnvironment, CMake
from conans.tools import download, untargz, check_sha1, replace_in_file, environment_append
import os
import shutil

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
    exports = "CMakeLists.txt"
    generators = "cmake", "txt"

    def config_options(self):
        del self.settings.compiler.libcxx

    def print_dir(self):
        self.output.info('dir: ' + os.getcwd())
        for root, _dirnames, filenames in os.walk('.'):
            for filename in filenames:
                self.output.info(" " + os.path.join(root, filename))

    def source(self):
        tarball_name = self.FOLDER_NAME + '.tar.gz'
        download("https://github.com/mongodb/libbson/releases/download/%s/%s.tar.gz"
                 % (self.version, self.FOLDER_NAME), tarball_name)
        check_sha1(tarball_name, "5c8119a7500a9131e0a6b0c7357bbac4069ade56")
        untargz(tarball_name)
        os.unlink(tarball_name)
        shutil.move("%s/CMakeLists.txt" % self.FOLDER_NAME, "%s/CMakeListsOriginal.cmake" % self.FOLDER_NAME)
        shutil.move("CMakeLists.txt", "%s/CMakeLists.txt" % self.FOLDER_NAME)

    def build(self):

        # cmake support is still experimental for unix
        if self.settings.os == "Windows":
            use_cmake = True
        else:
            use_cmake = False

        if use_cmake:
            cmake = CMake(self)
            if self.options.shared:
                cmake.definitions["ENABLE_STATIC"] = "OFF"
                cmake.definitions["ENABLE_TESTS"] = "OFF"
            else:
                cmake.definitions["ENABLE_STATIC"] = "ON"
            cmake.definitions["CMAKE_INSTALL_PREFIX"] = ("%s/%s/_inst" % (self.conanfile_directory, self.FOLDER_NAME))
            #cmake.configure(source_dir=("%s/%s" % (self.conanfile_directory, self.FOLDER_NAME)), build_dir=("%s/_inst" % (self.FOLDER_NAME)))
            cmake.configure(source_dir=("%s/%s" % (self.conanfile_directory, self.FOLDER_NAME)))
            cmake.build()
            cmake.install()
            self.print_dir()

        else:

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


    def package(self):
        self.print_dir()

        os.rename("%s/COPYING" % (self.FOLDER_NAME), "%s/LICENSE" % (self.FOLDER_NAME))
        self.copy("license*", src="%s" % (self.FOLDER_NAME), dst="licenses", ignore_case=True, keep_path=False)
        self.copy(pattern="*.h", dst="include", src="%s/_inst/include" % (self.FOLDER_NAME), keep_path=True)
        if self.options.shared:
            if self.settings.os == "Macos":
                self.copy(pattern="*.dylib", src="%s/_inst/lib" % (self.FOLDER_NAME), dst="lib", keep_path=False)
            elif self.settings.os == "Windows":
                self.copy(pattern="*.dll*", src="%s/_inst/bin" % (self.FOLDER_NAME), dst="bin", keep_path=False)
            else:
                self.copy(pattern="*.so*", src="%s/_inst/lib" % (self.FOLDER_NAME), dst="lib", keep_path=False)
        else:
            self.copy(pattern="*bson*.a", src="%s/_inst/lib" % (self.FOLDER_NAME), dst="lib", keep_path=False)
        if self.settings.os == "Windows":
            self.copy(pattern="*.lib*", src="%s/_inst/lib" % (self.FOLDER_NAME), dst="lib", keep_path=False)

    def package_info(self):
        if self.options.shared:
            self.cpp_info.libs = ['bson-1.0']
        else:
            self.cpp_info.libs = ['bson-static-1.0']
        self.cpp_info.includedirs = ['include/libbson-1.0']
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["pthread", "rt"])
        if self.settings.os == "Windows":
            if not self.options.shared:
                self.cpp_info.libs.extend(["ws2_32"])
                self.cpp_info.defines.append("BSON_STATIC=1")

