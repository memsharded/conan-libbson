from conans import ConanFile, CMake
import os

class LibbsonTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        # Current dir is "test_package/build/<build_id>" and CMakeLists.txt is in "test_package"
        cmake.configure(source_dir=self.conanfile_directory, build_dir="./")
        cmake.build()

    def imports(self):
        self.copy(pattern="*.dll", dst="bin", src="bin")
        self.copy(pattern="*.lib", dst="lib", src="lib")
        self.copy(pattern="*.so", dst="bin", src="lib")
        self.copy(pattern="*.dylib", dst="bin", src="lib")

    def test(self):
        os.chdir("bin")
        self.run(".%stestapp" % os.sep)
