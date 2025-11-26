# Progress Stepper Design Specification

## Problem Statement

Current CTkButton-based stepper confuses users:
- Blue active step looks clickable (same as action buttons)
- No visual feedback for completed steps
- All steps look like navigation buttons

## Solution: Frame-Based Progress Indicator

### Visual States

**Completed**: Green border + checkmark + bold text
**Active**: Orange border + bold text
**Upcoming**: Gray border + muted text

### Color Scheme

```python
# COMPLETED STEP
completed_bg = ("#e8f5e9", "#1b4d1b")      # Subtle green tint
completed_border = ("#4caf50", "#66bb6a")   # Green accent
completed_text = ("#2e7d32", "#81c784")     # Green text

# ACTIVE STEP
active_bg = ("gray95", "gray17")            # Neutral lift
active_border = ("#ff9800", "#ffb74d")      # Orange accent (NOT blue)
active_text = ("gray10", "gray95")          # High contrast

# UPCOMING STEP
upcoming_bg = ("gray92", "gray14")          # Recessed
upcoming_border = ("gray75", "gray25")      # Minimal contrast
upcoming_text = ("gray50", "gray50")        # Muted
```

### Implementation Code

```python
import customtkinter as ctk

class ProgressStepper(ctk.CTkFrame):
    def __init__(self, parent, steps, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.steps = steps
        self.current_step = 0
        self.step_frames = []

        # Container for steps
        self.stepper_container = ctk.CTkFrame(self, fg_color="transparent")
        self.stepper_container.pack(fill="x", padx=20, pady=10)

        self._create_steps()

    def _create_steps(self):
        for i, step_text in enumerate(self.steps):
            # Step frame (replaces button)
            step_frame = ctk.CTkFrame(
                self.stepper_container,
                corner_radius=8,
                fg_color=("gray92", "gray14"),  # Default: upcoming
                border_width=2,
                border_color=("gray75", "gray25")
            )
            step_frame.pack(side="left", padx=5, ipadx=12, ipady=8)

            # Step label
            step_label = ctk.CTkLabel(
                step_frame,
                text=f"{i+1}. {step_text}",
                font=ctk.CTkFont(size=13, weight="normal"),
                text_color=("gray50", "gray50")
            )
            step_label.pack()

            self.step_frames.append({
                "frame": step_frame,
                "label": step_label,
                "status": "upcoming"
            })

            # Arrow separator (except after last step)
            if i < len(self.steps) - 1:
                arrow = ctk.CTkLabel(
                    self.stepper_container,
                    text="→",
                    font=ctk.CTkFont(size=16),
                    text_color=("gray60", "gray40")
                )
                arrow.pack(side="left", padx=8)

    def update_step(self, step_index):
        """Update stepper to show current step"""
        self.current_step = step_index

        for i, step in enumerate(self.step_frames):
            if i < step_index:
                # COMPLETED
                step["frame"].configure(
                    fg_color=("#e8f5e9", "#1b4d1b"),
                    border_color=("#4caf50", "#66bb6a")
                )
                step["label"].configure(
                    text=f"✓ {i+1}. {self.steps[i]}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=("#2e7d32", "#81c784")
                )
                step["status"] = "completed"

            elif i == step_index:
                # ACTIVE
                step["frame"].configure(
                    fg_color=("gray95", "gray17"),
                    border_color=("#ff9800", "#ffb74d")
                )
                step["label"].configure(
                    text=f"{i+1}. {self.steps[i]}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=("gray10", "gray95")
                )
                step["status"] = "active"

            else:
                # UPCOMING
                step["frame"].configure(
                    fg_color=("gray92", "gray14"),
                    border_color=("gray75", "gray25")
                )
                step["label"].configure(
                    text=f"{i+1}. {self.steps[i]}",
                    font=ctk.CTkFont(size=13, weight="normal"),
                    text_color=("gray50", "gray50")
                )
                step["status"] = "upcoming"


# USAGE EXAMPLE
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.stepper = ProgressStepper(
            self,
            steps=["Configure", "Calculate Size", "Download"]
        )
        self.stepper.pack(fill="x", pady=10)

        # Start at step 0 (Configure)
        self.stepper.update_step(0)

        # Action buttons (notice the blue color - distinct from stepper)
        action_btn = ctk.CTkButton(
            self,
            text="Start Download",
            fg_color=("#1f538d", "#3b8ed0"),  # Blue = clickable action
            height=40
        )
        action_btn.pack(pady=20)

if __name__ == "__main__":
    app = App()
    app.mainloop()
```

### Simpler Label-Based Alternative

```python
class SimpleProgressStepper(ctk.CTkFrame):
    def __init__(self, parent, steps, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.steps = steps
        self.current_step = 0
        self.step_labels = []

        # Container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=10)

        for i, step_text in enumerate(steps):
            # Step label
            label = ctk.CTkLabel(
                container,
                text=f"{i+1}. {step_text}",
                font=ctk.CTkFont(size=13, weight="normal"),
                text_color=("gray50", "gray50")
            )
            label.pack(side="left", padx=8)
            self.step_labels.append(label)

            # Arrow separator
            if i < len(steps) - 1:
                arrow = ctk.CTkLabel(
                    container,
                    text="→",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray60", "gray40")
                )
                arrow.pack(side="left", padx=8)

    def update_step(self, step_index):
        """Update to current step"""
        self.current_step = step_index

        for i, label in enumerate(self.step_labels):
            if i < step_index:
                # Completed: green + checkmark
                label.configure(
                    text=f"✓ {i+1}. {self.steps[i]}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=("#2e7d32", "#81c784")
                )
            elif i == step_index:
                # Active: orange + bold
                label.configure(
                    text=f"{i+1}. {self.steps[i]}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=("#ff9800", "#ffb74d")
                )
            else:
                # Upcoming: gray + normal
                label.configure(
                    text=f"{i+1}. {self.steps[i]}",
                    font=ctk.CTkFont(size=13, weight="normal"),
                    text_color=("gray50", "gray50")
                )
```

## Visual Comparison

### Before (CTkButton-based)
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 1. Configure │  │2. Calculate  │  │ 3. Download  │
│   (BLUE)     │  │   (GRAY)     │  │   (GRAY)     │
└──────────────┘  └──────────────┘  └──────────────┘
❌ All look like clickable buttons
❌ Blue active step blends with action buttons
❌ No visual feedback for completed steps
```

### After (Frame-based)
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│✓ Configure │  →   │Calculate Size│  →   │  Download   │
│ (GREEN)    │      │  (ORANGE)    │      │   (GRAY)    │
└─────────────┘      └──────────────┘      └─────────────┘
✓ Clear status indicators, not buttons
✓ Distinct colors for each state
✓ Checkmark shows completion
✓ Orange active step distinct from blue action buttons
```

## Key Benefits

1. **Component Choice**: Frames/Labels = display-only (not interactive)
2. **Color Semantics**: Green (done) / Orange (current) / Gray (pending) / Blue (action buttons only)
3. **Visual Indicators**: Checkmarks provide instant completion feedback
4. **Border Highlights**: Active step uses border (not fill) to avoid button appearance
5. **Typography**: Bold for active/completed creates clear hierarchy

## Recommendation

**Use Frame-based approach** for:
- Robust visual separation from buttons
- Clear state differentiation with borders
- Modern UI aesthetic
- Easier styling and future enhancements

**Use Label-based approach** if:
- Minimal visual weight needed
- Screen space is tight
- Compact design preferred

## Migration from Current Code

```python
# OLD - CTkButton approach
self.step1_btn = ctk.CTkButton(
    self.stepper_frame,
    text="1. Configure",
    fg_color=("#1f538d", "#3b8ed0"),  # Looks clickable
    state="disabled"
)

# NEW - CTkFrame approach
self.step1_frame = ctk.CTkFrame(
    self.stepper_frame,
    corner_radius=8,
    border_width=2,
    border_color=("#ff9800", "#ffb74d")  # Orange = active
)
self.step1_label = ctk.CTkLabel(
    self.step1_frame,
    text="1. Configure",
    font=ctk.CTkFont(size=13, weight="bold")
)
```

## Summary Table

| Aspect | Before | After |
|--------|--------|-------|
| Component | CTkButton | CTkFrame + CTkLabel |
| Active Color | Blue (#3b8ed0) | Orange (#ffb74d) border |
| Completed | Gray (disabled) | Green (#66bb6a) + checkmark ✓ |
| Upcoming | Gray (disabled) | Gray (muted text) |
| Clickable? | Looks clickable | Clearly read-only |
| Distinct from actions? | No (same blue) | Yes (orange/green vs blue) |
