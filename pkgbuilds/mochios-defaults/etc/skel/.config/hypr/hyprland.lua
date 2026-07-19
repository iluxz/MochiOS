-- mochios default hyprland config

-- programs
local terminal = "kitty"
local fileManager = "dolphin"
local menu = "wofi --show drun"

-- mochios color palette
local colors = {
    bg      = "rgba(1a1025ee)",
    fg      = "rgba(e0d0f0ee)",
    primary = "rgba(7a3cb0ee)",
    accent  = "rgba(9664c8ee)",
    surface = "rgba(251635ee)",
    border  = "rgba(5a3a7eee)",
    error   = "rgba(cc3333ee)",
}

-- monitors
hl.monitor({
    output   = "",
    mode     = "preferred",
    position = "auto",
    scale    = "auto",
})

-- environment
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("QT_WAYLAND_DISABLE_WINDOWDECORATION", "1")
hl.env("GDK_BACKEND", "wayland,x11")
hl.env("XDG_CURRENT_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_TYPE", "wayland")

-- general settings
hl.config({
    general = {
        gaps_in           = 5,
        gaps_out          = 15,
        border_size       = 2,
        col = {
            active_border   = { colors = {colors.primary, colors.accent}, angle = 45 },
            inactive_border = colors.border,
        },
        cursor_inactive_timeout = 3,
        layout = "dwindle",
        resize_on_border = false,
    },
    decoration = {
        rounding      = 8,
        active_opacity   = 1.0,
        inactive_opacity = 0.9,
        shadow = {
            enabled = true,
            range   = 8,
            render_power = 3,
            color   = "rgba(1a102566)",
        },
        blur = {
            enabled     = true,
            size        = 3,
            passes      = 2,
            new_optimizations = true,
            noise       = 0.01,
            contrast    = 0.9,
            brightness  = 0.8,
            popups      = true,
            popups_ignorealpha = 0.2,
        },
    },
    input = {
        kb_layout     = "us",
        follow_mouse  = 1,
        sensitivity   = 0,
        accel_profile = "flat",
        touchpad = {
            natural_scroll = true,
            disable_while_typing = true,
        },
    },
    gestures = {
        workspace_swipe       = true,
        workspace_swipe_fingers = 3,
    },
    group = {
        groupbar = {
            enabled = true,
            gradients = false,
            col = {
                active           = colors.primary,
                inactive         = colors.surface,
                locked_active    = colors.accent,
                locked_inactive  = colors.surface,
            },
        },
    },
    misc = {
        disable_autoreload      = true,
        disable_hyprland_logo   = true,
        vfr                     = true,
        vrr                     = 1,
        enable_swallow          = true,
        swallow_regex           = "^(kitty)$",
        animate_mouse_windowdragging = true,
        focus_on_activate       = true,
    },
    dwindle = {
        pseudotile              = true,
        preserve_split          = true,
        smart_split             = false,
        smart_resizing          = true,
        default_split_count     = 2,
    },
    master = {
        allow_small_split       = true,
        mfact                   = 0.5,
        orientation             = "center",
        smart_resizing          = true,
    },
    binds = {
        allow_workspace_cycles  = true,
        pass_mouse_when_bound   = false,
        scroll_event_delay      = 300,
    },
})

-- window rules
hl.window_rule({
    match = { class = ".*" },
    set   = { border_size = 2 },
})
hl.window_rule({
    match = { title = "^(.*)(——|—|:|»)(.*)(float|pop)(.*)$" },
    set   = { floating = true, pin = true },
})
hl.window_rule({
    match = { class = "(wofi|rofi|dmenu)" },
    set   = { floating = true, pin = true, no_focus = true, border_size = 1 },
})
hl.window_rule({
    match = { class = "(xdg-desktop-portal-hyprland|xdg-desktop-portal-gtk)" },
    set   = { floating = true, pin = true },
})
hl.window_rule({
    match = { class = "(pavucontrol|blueman-manager|qt5ct|qt6ct)" },
    set   = { floating = true, pin = true },
})
hl.window_rule({
    match = { class = "(polkit-gnome-authentication-agent-1)" },
    set   = { floating = true, pin = true, no_focus = true },
})
hl.window_rule({
    match = { class = "(firefox|chromium|google-chrome|brave)" },
    set   = { opacity = 1.0, inactive_opacity = 1.0 },
})

-- keybinds
local mod = "SUPER"
local shift = "SUPER_SHIFT"
local ctrl = "SUPER_CTRL"
local alt = "SUPER_ALT"

-- launcher
hl.bind(mod, "Return", hl.dsp.exec_cmd(terminal))
hl.bind(mod, "D", hl.dsp.exec_cmd(menu))
hl.bind(mod, "E", hl.dsp.exec_cmd(fileManager))
hl.bind(mod, "Q", hl.dsp.window.close())
hl.bind(mod, "F", hl.dsp.window.toggle_fullscreen())
hl.bind(mod, "V", hl.dsp.window.toggle_floating())

-- kill / quit
hl.bind(shift, "Q", hl.dsp.exec_cmd("hyprctl kill"))
hl.bind(shift, "E", hl.dsp.exit())

-- screenshot
hl.bind(ctrl, "S", hl.dsp.exec_cmd("grim -g \"$(slurp)\" - | wl-copy"))
hl.bind(shift, "S", hl.dsp.exec_cmd("grim - | wl-copy"))

-- focus movement
hl.bind(mod, "left",  hl.dsp.window.move_focus("l"))
hl.bind(mod, "right", hl.dsp.window.move_focus("r"))
hl.bind(mod, "up",    hl.dsp.window.move_focus("u"))
hl.bind(mod, "down",  hl.dsp.window.move_focus("d"))

-- window movement
hl.bind(shift, "left",  hl.dsp.window.move("l"))
hl.bind(shift, "right", hl.dsp.window.move("r"))
hl.bind(shift, "up",    hl.dsp.window.move("u"))
hl.bind(shift, "down",  hl.dsp.window.move("d"))

-- workspace switching
for i = 1, 10 do
    hl.bind(mod, tostring(i % 10), hl.dsp.workspace.switch(i))
    hl.bind(shift, tostring(i % 10), hl.dsp.window.move_to_workspace(i))
end

-- special workspace (scratchpad)
hl.bind(mod, "grave", hl.dsp.workspace.toggle_special())
hl.bind(shift, "grave", hl.dsp.window.move_to_special())

-- monitor movement
hl.bind(ctrl, "left",  hl.dsp.workspace.move_to_monitor("l"))
hl.bind(ctrl, "right", hl.dsp.workspace.move_to_monitor("r"))

-- resize mode
hl.bind(alt, "right", hl.dsp.submap("resize"))

hl.define_submap("resize", function()
    hl.bind("right", hl.dsp.window.resize({ x = 20, y = 0 }), { repeating = true })
    hl.bind("left",  hl.dsp.window.resize({ x = -20, y = 0 }), { repeating = true })
    hl.bind("up",    hl.dsp.window.resize({ x = 0, y = -20 }), { repeating = true })
    hl.bind("down",  hl.dsp.window.resize({ x = 0, y = 20 }), { repeating = true })
    hl.bind("escape", hl.dsp.submap("reset"))
    hl.bind("Return", hl.dsp.submap("reset"))
end)

-- layout
hl.bind(mod, "T", hl.dsp.layout.set("master"))
hl.bind(shift, "T", hl.dsp.layout.set("dwindle"))

-- scroll through workspaces
hl.bind(mod, "mouse_up",   hl.dsp.workspace.switch("+1"))
hl.bind(mod, "mouse_down", hl.dsp.workspace.switch("-1"))

-- autostart
hl.on("hyprland.start", function()
    hl.exec_cmd("mochi-wallpaper")
    hl.exec_cmd("waybar")
    hl.exec_cmd("polkit-kde-authentication-agent-1")
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("dunst")
end)
