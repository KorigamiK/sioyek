#ifndef OPEN_WITH_APP_H
#define OPEN_WITH_APP_H

#include <QApplication>
#include <QFileOpenEvent>
#include <QStringList>

class OpenWithApplication : public QApplication
{
    Q_OBJECT
public:
    OpenWithApplication(int& argc, char** argv)
        : QApplication(argc, argv)
    {
    }

    // macOS can deliver QFileOpenEvent(s) before any handler is connected to
    // `file_ready` (e.g. on a cold launch triggered by "Open with" in Finder).
    // We buffer those file names and replay them once a receiver is ready.
    void flush_pending_files() {
        has_receiver = true;
        QStringList files = std::move(pending_files);
        pending_files.clear();
        for (const QString& file : files) {
            emit file_ready(file);
        }
    }

signals:
    void file_ready(const QString& file_name);

protected:
    bool event(QEvent* event) override;

private:
    QStringList pending_files;
    bool has_receiver = false;
};

#endif // OPEN_WITH_APP_H
