#include <OpenWithApplication.h>

bool OpenWithApplication::event(QEvent* event) {
    if (event->type() == QEvent::FileOpen) {
        QFileOpenEvent* openEvent = static_cast<QFileOpenEvent*>(event);
        if (has_receiver) {
            emit file_ready(openEvent->file());
        }
        else {
            // The event loop isn't ready to open files yet (cold launch from
            // Finder). Remember it and replay once flush_pending_files() runs.
            pending_files.append(openEvent->file());
        }
    }

    return QApplication::event(event);
}
