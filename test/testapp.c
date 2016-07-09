#include <bson.h>
#include <stdio.h>

int
main(int argc, char **argv)
{
	uint8_t buf[] = { 0x0b, 0, 0, 0, 0x0a, 0x6e, 0x75, 0x6c, 0x6c, 0, 0 };
	bson_reader_t* reader = bson_reader_new_from_data(buf, sizeof(buf));
	if (reader)
		bson_reader_destroy(reader);
	printf("done\n");
	return 0;
}
