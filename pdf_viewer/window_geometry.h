#pragma once

#include <QList>
#include <QRect>

inline bool has_visible_window_area(const QRect& geometry, const QList<QRect>& screens) {
    if (!geometry.isValid()) {
        return false;
    }
    for (const QRect& screen : screens) {
        const QRect visible = geometry.intersected(screen);
        // Window managers can park inactive windows with only a pixel showing.
        if (visible.width() >= qMin(64, geometry.width()) &&
            visible.height() >= qMin(64, geometry.height())) {
            return true;
        }
    }
    return false;
}

inline QRect window_geometry_on_screen(const QRect& geometry, const QList<QRect>& screens,
                                      const QRect& fallback = QRect()) {
    if (screens.isEmpty() || has_visible_window_area(geometry, screens)) {
        return geometry;
    }
    if (has_visible_window_area(fallback, screens)) {
        return fallback;
    }

    // Screens are ordered with the primary screen first. Preserve the window's
    // size where possible, but make it fit when a larger monitor was removed.
    const QRect screen = screens.first();
    const QSize size = geometry.isValid() ? geometry.size() : QSize(800, 600);
    QRect recovered(QPoint(), size.boundedTo(screen.size()));
    recovered.moveCenter(screen.center());
    return recovered;
}
