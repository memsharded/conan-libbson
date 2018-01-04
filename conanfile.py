from conans import ConanFile, AutoToolsBuildEnvironment, CMake, tools
import os

class LibbsonConan(ConanFile):
    name = "libbson"
    version = "1.8.1"
    url = "https://github.com/theirix/conan-libbson"
    license = "https://github.com/mongodb/libbson/blob/master/COPYING"
    description = "A BSON utility library."
    FOLDER_NAME = 'libbson-%s' % version
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake", "txt"

    def config_options(self):
        del self.settings.compiler.libcxx

    def source(self):
        tools.get("https://github.com/mongodb/libbson/releases/download/%s/%s.tar.gz"
                 % (self.version, self.FOLDER_NAME))
        os.rename("%s/CMakeLists.txt" % self.FOLDER_NAME, "%s/CMakeListsOriginal.txt" % self.FOLDER_NAME)
        os.rename("CMakeLists.txt", "%s/CMakeLists.txt" % self.FOLDER_NAME)

    def build(self):
        # cmake support is still experimental for unix
        use_cmake = self.settings.os == "Windows"

        if use_cmake:
            cmake = CMake(self)
            cmake.definitions["ENABLE_STATIC"] = not self.options.shared
            cmake.definitions["ENABLE_TESTS"] = False
            cmake.definitions["CMAKE_INSTALL_PREFIX"] = ("%s/%s/_inst" % (self.build_folder, self.FOLDER_NAME))
            cmake.configure(source_folder=self.FOLDER_NAME)
            cmake.build()
            cmake.install()

        else:

            env_build = AutoToolsBuildEnvironment(self)

            # compose configure options
            suffix = ''
            if self.options.shared:
                suffix += " --enable-shared --disable-static"
            else:
                suffix += " --disable-shared --enable-static"

            with tools.environment_append(env_build.vars):
                with tools.chdir(os.path.join(self.FOLDER_NAME)):
                    # refresh configure
                    cmd = 'autoreconf --force --verbose --install -I build/autotools'
                    self.run(cmd)

                    # disable rpath build
                    tools.replace_in_file("configure", r"-install_name \$rpath/", "-install_name ")

                    cmd = './configure --prefix=%s/%s/_inst %s' % (self.build_folder, self.FOLDER_NAME, suffix)
                    self.output.warn('Running: ' + cmd)
                    self.run(cmd)

                    cmd = 'make install'
                    self.output.warn('Running: ' + cmd)
                    self.run(cmd)


    def package(self):
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
