from conans import ConanFile, AutoToolsBuildEnvironment, CMake, tools
import os, shutil

class LibbsonConan(ConanFile):
    name = "libbson"
    version = "1.9.2"
    url = "https://github.com/theirix/conan-libbson"
    license = "Apache License 2.0 (https://github.com/mongodb/libbson/blob/master/COPYING)"
    homepage = "https://github.com/mongodb/libbson"
    description = "A BSON utility library."
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake", "txt"

    def config_options(self):
        del self.settings.compiler.libcxx

    def source(self):
        tools.get("https://github.com/mongodb/libbson/releases/download/%s/libbson-%s.tar.gz"
                  % (self.version, self.version))
        os.rename("libbson-%s" % self.version, "sources")
        os.rename("sources/CMakeLists.txt", "sources/CMakeListsOriginal.txt")
        shutil.copy("CMakeLists.txt", "sources/CMakeLists.txt")

    def build(self):
        # cmake support is still experimental for unix
        use_cmake = self.settings.os == "Windows"

        if use_cmake:
            cmake = CMake(self)
            # upstream cmake is flawed and doesn't understand boolean values other than ON/OFF
            cmake.definitions["ENABLE_STATIC"] = "OFF" if self.options.shared else "ON"
            cmake.definitions["ENABLE_TESTS"] = False
            cmake.definitions["CMAKE_INSTALL_PREFIX"] = ("%s/_inst" % self.build_folder)
            cmake.verbose = True
            cmake.configure(source_folder="sources")
            cmake.build()
            cmake.install()

        else:

            env_build = AutoToolsBuildEnvironment(self)

            # compose configure options
            configure_args = ['--prefix=%s/_inst' % self.build_folder]
            if self.options.shared:
                configure_args.extend(["--enable-shared", "--disable-static"])
            else:
                configure_args.extend(["--disable-shared", "--enable-static"])

            with tools.chdir("sources"):
                # refresh configure
                self.run('autoreconf --force --verbose --install -I build/autotools')

                # disable rpath build
                tools.replace_in_file("configure", r"-install_name \$rpath/", "-install_name ")

                env_build.configure(args=configure_args)

                env_build.make(args=['install'])


    def package(self):
        self.copy("copying*", src="sources", dst="licenses", ignore_case=True, keep_path=False)
        self.copy(pattern="*.h", dst="include", src="_inst/include", keep_path=True)
        if self.options.shared:
            if self.settings.os == "Macos":
                self.copy(pattern="*.dylib", src="_inst/lib", dst="lib", keep_path=False)
            elif self.settings.os == "Windows":
                self.copy(pattern="*.dll*", src="_inst/bin", dst="bin", keep_path=False)
            else:
                self.copy(pattern="*.so*", src="_inst/lib", dst="lib", keep_path=False)
        else:
            self.copy(pattern="*bson*.a", src="_inst/lib", dst="lib", keep_path=False)
        if self.settings.os == "Windows":
            self.copy(pattern="*.lib*", src="_inst/lib", dst="lib", keep_path=False)

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
