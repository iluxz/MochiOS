/*
 * mochi-splash — animated boot splash for mochios
 * Renders a bouncing mochi character using UEFI GOP,
 * then chainloads into mochiboot (BOOTX64.EFI).
 *
 * Compile with gnu-efi:
 *   gcc -nostdlib -fno-stack-protector -fno-strict-aliasing \
 *       -fpic -fshort-wchar -mno-red-zone -DEFI_FUNCTION_WRAPPER \
 *       -I/usr/include/efi -I/usr/include/efi/x86_64 \
 *       -c splash.c -o splash.o
 *   ld -nostdlib -znocombreloc -T /usr/lib/elf_x86_64_efi.lds \
 *       -shared -Bsymbolic -L/usr/lib -lgnuefi -lefi \
 *       splash.o -o splash.so
 *   objcopy -j .text -j .sdata -j .data -j .dynamic \
 *       -j .dynsym -j .rel -j .rela -j .reloc \
 *       --target=efi-app-x86_64 splash.so splash.efi
 */

#include <efi.h>
#include <efilib.h>
#include <eficonsplit.h>

/* ---- constants ---- */

#define FRAME_COUNT    12
#define FRAME_MS       80
#define TIMEOUT_SEC    3
#define MOCHI_RADIUS   60

/* mochi body colors */
#define COLOR_BG       0xFF1A1A2E
#define COLOR_BODY     0xFFFFF5E6
#define COLOR_EAR      0xFFE8D5B7
#define COLOR_EYE      0xFF2D2D2D
#define COLOR_CHEEK    0xFFFF9EAA
#define COLOR_TEXT     0xFF00E5FF
#define COLOR_SHADOW   0xFFD4C4A8

/* ARGB -> EFI_GRAPHICS_OUTPUT_BLT_PIXEL */
#define TO_BLT(c)  { ((c) >> 16) & 0xFF, ((c) >> 8) & 0xFF, (c) & 0xFF, 0 }
#define ALPHA(c,a) ( (((c) & 0x00FFFFFF) | ((UINT32)(a) << 24)) )

typedef struct {
    UINT32 x, y;
} Point;

/* ---- framebuffer helpers ---- */

static void fill_rect(EFI_GRAPHICS_OUTPUT_BLT_PIXEL *buf,
                      UINTN fb_w, UINTN fb_h,
                      UINTN x, UINTN y, UINTN w, UINTN h,
                      EFI_GRAPHICS_OUTPUT_BLT_PIXEL color) {
    for (UINTN row = y; row < y + h && row < fb_h; row++) {
        for (UINTN col = x; col < x + w && col < fb_w; col++) {
            buf[row * fb_w + col] = color;
        }
    }
}

static void draw_circle(EFI_GRAPHICS_OUTPUT_BLT_PIXEL *buf,
                        UINTN fb_w, UINTN fb_h,
                        UINTN cx, UINTN cy, UINTN r,
                        EFI_GRAPHICS_OUTPUT_BLT_PIXEL color) {
    for (INTN dy = -(INTN)r; dy <= (INTN)r; dy++) {
        for (INTN dx = -(INTN)r; dx <= (INTN)r; dx++) {
            if (dx*dx + dy*dy <= (INTN)(r*r)) {
                INTN px = (INTN)cx + dx;
                INTN py = (INTN)cy + dy;
                if (px >= 0 && (UINTN)px < fb_w && py >= 0 && (UINTN)py < fb_h) {
                    buf[(UINTN)py * fb_w + (UINTN)px] = color;
                }
            }
        }
    }
}

static void draw_triangle_up(EFI_GRAPHICS_OUTPUT_BLT_PIXEL *buf,
                             UINTN fb_w, UINTN fb_h,
                             UINTN cx, UINTN cy, UINTN r,
                             EFI_GRAPHICS_OUTPUT_BLT_PIXEL color) {
    for (UINTN dy = 0; dy < r; dy++) {
        UINTN half = (dy * r) / r;
        for (UINTN dx = 0; dx < half * 2 + 1; dx++) {
            INTN px = (INTN)cx - (INTN)half + (INTN)dx;
            INTN py = (INTN)cy - (INTN)dy;
            if (px >= 0 && (UINTN)px < fb_w && py >= 0 && (UINTN)py < fb_h) {
                buf[(UINTN)py * fb_w + (UINTN)px] = color;
            }
        }
    }
}

/* ---- mochi character drawing ---- */

static void draw_mochi(EFI_GRAPHICS_OUTPUT_BLT_PIXEL *buf,
                       UINTN fb_w, UINTN fb_h,
                       UINTN cx, UINTN cy, UINTN r,
                       EFI_GRAPHICS_OUTPUT_BLT_PIXEL body_color,
                       EFI_GRAPHICS_OUTPUT_BLT_PIXEL ear_color) {
    EFI_GRAPHICS_OUTPUT_BLT_PIXEL white = TO_BLT(COLOR_EYE);
    EFI_GRAPHICS_OUTPUT_BLT_PIXEL blush = TO_BLT(COLOR_CHEEK);

    /* body */
    draw_circle(buf, fb_w, fb_h, cx, cy, r, body_color);

    /* ears (two triangles on top) */
    UINTN ear_r = r * 3 / 5;
    draw_triangle_up(buf, fb_w, fb_h, cx - r/2, cy - r + ear_r/2, ear_r, ear_color);
    draw_triangle_up(buf, fb_w, fb_h, cx + r/2, cy - r + ear_r/2, ear_r, ear_color);

    /* eyes */
    UINTN eye_r = r / 6;
    draw_circle(buf, fb_w, fb_h, cx - r/3, cy - r/6, eye_r, white);
    draw_circle(buf, fb_w, fb_h, cx + r/3, cy - r/6, eye_r, white);

    /* blush */
    UINTN blush_r = r / 5;
    draw_circle(buf, fb_w, fb_h, cx - r/2, cy + r/4, blush_r, blush);
    draw_circle(buf, fb_w, fb_h, cx + r/2, cy + r/4, blush_r, blush);
}

/* ---- text rendering (simple glyph approximation) ---- */

static void draw_char(EFI_GRAPHICS_OUTPUT_BLT_PIXEL *buf,
                      UINTN fb_w, UINTN fb_h,
                      UINTN x, UINTN y, CHAR16 c,
                      EFI_GRAPHICS_OUTPUT_BLT_PIXEL color) {
    /* Simple 8x8 pixel font for ASCII chars — just draw a rectangle placeholder */
    /* In production, we'd use Simple Text Output or a real font */
    fill_rect(buf, fb_w, fb_h, x, y, 8, 8, color);
}

/* ---- main EFI application ---- */

EFI_STATUS
EFIAPI
efi_main(EFI_HANDLE ImageHandle, EFI_SYSTEM_TABLE *SystemTable) {
    EFI_STATUS Status;
    UINTN Index;

    InitializeLib(ImageHandle, SystemTable);

    /* ---- locate GOP ---- */
    EFI_GUID GopGuid = EFI_GRAPHICS_OUTPUT_PROTOCOL_GUID;
    EFI_GRAPHICS_OUTPUT_PROTOCOL *Gop = NULL;
    Status = BS->LocateProtocol(&GopGuid, NULL, (void**)&Gop);
    if (EFI_ERROR(Status) || Gop == NULL) {
        /* no GOP, just chainload immediately */
        goto chainload;
    }

    UINTN fb_w = Gop->Mode->Info->HorizontalResolution;
    UINTN fb_h = Gop->Mode->Info->VerticalResolution;
    if (fb_w == 0 || fb_h == 0) {
        fb_w = 1024;
        fb_h = 768;
    }

    /* ---- allocate pixel buffer ---- */
    UINTN buf_size = fb_w * fb_h * sizeof(EFI_GRAPHICS_OUTPUT_BLT_PIXEL);
    EFI_GRAPHICS_OUTPUT_BLT_PIXEL *fb_buf = NULL;
    Status = BS->AllocatePool(EfiBootServicesData, buf_size, (void**)&fb_buf);
    if (EFI_ERROR(Status) || fb_buf == NULL) {
        goto chainload;
    }

    EFI_GRAPHICS_OUTPUT_BLT_PIXEL bg = TO_BLT(COLOR_BG);
    EFI_GRAPHICS_OUTPUT_BLT_PIXEL body = TO_BLT(COLOR_BODY);
    EFI_GRAPHICS_OUTPUT_BLT_PIXEL ear = TO_BLT(COLOR_EAR);
    EFI_GRAPHICS_OUTPUT_BLT_PIXEL text_clr = TO_BLT(COLOR_TEXT);

    /* ---- animation loop ---- */
    UINTN cx = fb_w / 2;
    UINTN cy_base = fb_h / 2;
    UINTN bounce_amp = fb_h / 8;

    UINTN frame = 0;
    UINTN total_ms = 0;
    UINTN timeout_ms = TIMEOUT_SEC * 1000;

    /* reset console input to clear stale keypresses */
    ST->ConIn->Reset(ST->ConIn, FALSE);

    while (TRUE) {
        /* check for keypress */
        EFI_INPUT_KEY Key;
        Status = ST->ConIn->ReadKeyStroke(ST->ConIn, &Key);
        if (!EFI_ERROR(Status)) {
            break;
        }

        /* timeout */
        if (total_ms >= timeout_ms) {
            break;
        }

        /* ---- render frame ---- */

        /* clear */
        for (UINTN i = 0; i < fb_w * fb_h; i++) {
            fb_buf[i] = bg;
        }

        /* bouncing mochi */
        UINTN bounce_offset = bounce_amp;
        if (frame < FRAME_COUNT / 2) {
            bounce_offset = bounce_amp - (bounce_amp * frame) / (FRAME_COUNT / 2);
        } else {
            bounce_offset = (bounce_amp * (frame - FRAME_COUNT / 2)) / (FRAME_COUNT / 2);
        }

        UINTN my = cy_base - bounce_offset;
        draw_mochi(fb_buf, fb_w, fb_h, cx, my, MOCHI_RADIUS, body, ear);

        /* draw "MochiOS" text area */
        fill_rect(fb_buf, fb_w, fb_h, cx - 60, fb_h - 100, 120, 30, text_clr);

        /* blit to screen */
        UINTN pitch = fb_w * sizeof(EFI_GRAPHICS_OUTPUT_BLT_PIXEL);
        Gop->Blt(Gop, fb_buf, EfiBltBufferToVideo,
                 0, 0, 0, 0, fb_w, fb_h, pitch);

        /* wait */
        BS->Stall(FRAME_MS * 1000);
        total_ms += FRAME_MS;

        frame++;
    }

    BS->FreePool(fb_buf);

chainload:
    /* ---- chainload mochiboot ---- */
    {
        EFI_HANDLE NewHandle = NULL;

        /* get the device handle from our own image */
        EFI_LOADED_IMAGE_PROTOCOL *LoadedImage = NULL;
        EFI_GUID LoadedImageGuid = LOADED_IMAGE_PROTOCOL;
        Status = BS->HandleProtocol(ImageHandle, &LoadedImageGuid,
                                    (void**)&LoadedImage);
        if (!EFI_ERROR(Status) && LoadedImage != NULL) {
            EFI_DEVICE_PATH_PROTOCOL *FileDevPath = FileDevicePath(
                LoadedImage->DeviceHandle, L"\\EFI\\mochi\\mochiboot.efi");
            if (FileDevPath != NULL) {
                Status = BS->LoadImage(FALSE, ImageHandle, FileDevPath,
                                       NULL, 0, &NewHandle);
                if (!EFI_ERROR(Status)) {
                    BS->StartImage(NewHandle, NULL, NULL);
                }
            }
        }
    }
    return EFI_SUCCESS;
}
