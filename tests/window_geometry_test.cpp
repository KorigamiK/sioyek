#include "window_geometry.h"
#include <cstdio>

int main() {
    int failures = 0;
    auto check = [&](bool condition, const char* name) {
        if (!condition) {
            std::fprintf(stderr, "FAIL: %s\n", name);
            ++failures;
        }
    };
    const QRect primary(0, 25, 1440, 850);
    const QList<QRect> screens{primary};
    const QRect visible(100, 100, 1000, 700);
    const QRect lost(-1916, -171, 1270, 1049);
    const QRect recovered = window_geometry_on_screen(lost, screens);
    check(primary.contains(recovered), "recover reported off-screen coordinates and fit oversized window");
    check(window_geometry_on_screen(visible, screens) == visible, "preserve usable window position");
    check(window_geometry_on_screen(lost, screens, visible) == visible, "prefer last usable saved geometry");
    check(primary.contains(window_geometry_on_screen(lost, screens, lost)), "reject off-screen fallback");
    check(primary.contains(window_geometry_on_screen(QRect(), screens)), "recover invalid saved size");
    check(window_geometry_on_screen(lost, {}) == lost, "leave geometry alone when no screens exist");

    const QRect left(-1920, 0, 1920, 1080);
    const QRect above(0, -1080, 1920, 1080);
    const QRect on_left(-1800, 100, 1000, 700);
    const QRect on_top(100, -1000, 1000, 700);
    check(window_geometry_on_screen(on_left, {primary, left}) == on_left, "allow negative coordinates on connected left monitor");
    check(window_geometry_on_screen(on_top, {primary, above}) == on_top, "allow negative coordinates on connected upper monitor");
    check(primary.contains(window_geometry_on_screen(on_left, screens)), "recover after external monitor disconnects");

    const QRect parked(1439, 874, 1000, 700);
    check(!has_visible_window_area(parked, screens), "reject one-pixel workspace parking position");
    check(primary.contains(window_geometry_on_screen(parked, screens)), "recover workspace parking position");
    const QRect spanning(-200, 100, 1000, 700);
    check(window_geometry_on_screen(spanning, screens) == spanning, "preserve partially visible windows");
    const QRect gap(1500, 100, 500, 500);
    check(primary.contains(window_geometry_on_screen(gap, {primary, QRect(2500, 0, 1440, 900)})), "do not treat gaps between monitors as screens");
    check(has_visible_window_area(QRect(100, 100, 30, 30), screens), "allow small fully visible windows");
    return failures ? 1 : 0;
}
