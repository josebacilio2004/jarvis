package com.starkindustries.jarvis;

import android.content.Context;
import android.util.AttributeSet;
import android.view.View;
import android.webkit.WebView;

/**
 * Custom WebView that preserves HTML5 Audio & JS Execution when minimized or locked.
 */
public class BackgroundAudioWebView extends WebView {

    public BackgroundAudioWebView(Context context) {
        super(context);
    }

    public BackgroundAudioWebView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    public BackgroundAudioWebView(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
    }

    @Override
    protected void onWindowVisibilityChanged(int visibility) {
        // Keep audio streaming active even when activity loses focus or minimizes
        super.onWindowVisibilityChanged(View.VISIBLE);
    }
}
