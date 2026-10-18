#include <AppKit/AppKit.h>
#include <QWidget>
#import <Cocoa/Cocoa.h>

extern "C" void enableWindowDragGesture(WId winId) {
    if (winId == 0) return;
    NSWindow* window = [(NSView*)winId window];
    if (window == nil) return;

    // Window flags can recreate the native window. Keep weak references to each
    // registered main/helper window rather than retaining obsolete NSWindows.
    static NSHashTable<NSWindow*>* windows = [[NSHashTable alloc]
        initWithOptions:NSPointerFunctionsWeakMemory capacity:0];
    [windows addObject:window];

    static bool dragging_window = false;
    static id monitor = [NSEvent addLocalMonitorForEventsMatchingMask:
        NSEventMaskLeftMouseDown | NSEventMaskLeftMouseDragged | NSEventMaskLeftMouseUp
        handler:^NSEvent*(NSEvent* event) {
            if (event.type == NSEventTypeLeftMouseDown) {
                // A native drag may consume mouse-up itself. A fresh press
                // always ends the previous gesture in that case.
                dragging_window = false;
                NSEventModifierFlags modifiers = event.modifierFlags &
                    (NSEventModifierFlagCommand | NSEventModifierFlagControl |
                     NSEventModifierFlagOption | NSEventModifierFlagShift);
                if (modifiers == (NSEventModifierFlagCommand | NSEventModifierFlagControl)
                    && [windows containsObject:event.window]
                    && !(event.window.styleMask & NSWindowStyleMaskFullScreen)) {
                    dragging_window = true;
                    [event.window performWindowDragWithEvent:event];
                    return nil;
                }
            }
            else if (dragging_window) {
                if (event.type == NSEventTypeLeftMouseUp) {
                    dragging_window = false;
                }
                // Do not let Qt interpret the drag's release as a PDF click.
                return nil;
            }
            return event;
        }];
    (void)monitor;
}

extern "C" void showLookupForString(WId winId, const char* text, double x, double y) {
    if (winId == 0 || text == nullptr) return;

    NSView* view = (NSView*)winId;
    NSString* nsText = [NSString stringWithUTF8String:text];

    NSPoint point = NSMakePoint(x, y);

    [view showDefinitionForAttributedString:[[NSAttributedString alloc] initWithString:nsText]
                                    atPoint:point];
}

extern "C" void changeTitlebarColor(WId winId, double red, double green, double blue, double alpha){
    if (winId == 0) return;
    NSView* view = (NSView*)winId;
    NSWindow* window = [view window];
    window.titlebarAppearsTransparent = YES;
    window.backgroundColor = [NSColor colorWithRed:red green:green blue:blue alpha: alpha];
}
