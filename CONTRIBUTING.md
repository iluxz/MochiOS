# contributing

## what needs help

- **testing** — grab the latest ISO from CI artifacts and install it in a VM. report bugs.
- **packaging** — add packages to the `[mochi]` overlay repo
- **documentation** — the wiki is empty. fill it.
- **the installer** — mochiinstall gui and tui both have rough edges
- **mochiboot** — the bootloader could use better theme assets and config options
- **abroot** — the a/b update script is functional but could be more robust

## how to contribute

1. fork the repo
2. create a branch
3. make your changes
4. submit a PR

keep it simple. if it's a big change, open an issue first to discuss.

## code style

- python: whatever, just don't make it ugly
- go: `gofmt` before committing
- shell: `shellcheck` if you're feeling fancy
- PKGBUILDs: follow arch packaging standards
