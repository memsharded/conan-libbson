from conan.packager import ConanMultiPackager

if __name__ == "__main__":
    builder = ConanMultiPackager(username="theirix", channel="ci")
    builder.add_common_builds(shared_option_name="libbson:shared", pure_c=True)
    builder.run()
