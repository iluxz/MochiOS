CC      = gcc
LD      = ld
OBJCOPY = objcopy

EFI_ARCH = x86_64
ARCH_INC = /usr/include/efi/$(EFI_ARCH)
GNUEFI_INC = /usr/include/efi

CFLAGS  = -nostdlib -fno-stack-protector -fno-strict-aliasing \
          -fpic -fshort-wchar -mno-red-zone -DEFI_FUNCTION_WRAPPER \
          -I$(GNUEFI_INC) -I$(ARCH_INC) \
          -O2 -Wall -Wextra

LDFLAGS = -nostdlib -znocombreloc -T /usr/lib/elf_$(EFI_ARCH)_efi.lds \
          -shared -Bsymbolic -L/usr/lib \
          -lgnuefi -lefi

OBJS    = splash.o
TARGET  = mochi-splash.efi

all: $(TARGET)

splash.o: splash.c
	$(CC) $(CFLAGS) -c splash.c -o splash.o

$(TARGET): $(OBJS)
	$(LD) $(LDFLAGS) $(OBJS) -o splash.so
	$(OBJCOPY) -j .text -j .sdata -j .data -j .dynamic \
	           -j .dynsym -j .rel -j .rela -j .reloc \
	           --target=efi-app-$(EFI_ARCH) splash.so $(TARGET)
	rm -f splash.so

clean:
	rm -f $(OBJS) *.so $(TARGET)

.PHONY: all clean
