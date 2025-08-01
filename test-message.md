# Test Message for Markdown Rendering

## Inline Code Test
Here is some `inline code` that should have orange background.
Another example: `console.log('test')` should also be inline.

## Code Block Test
```javascript
function testFunction() {
    console.log('This should be a proper code block');
    return 'with gray background and copy button';
}
```

## Bold Text Test
This text should be **bold** and not treated as code.
Another example: **important note** should be bold.

## Mixed Content Test
Here we have `inline code`, **bold text**, and normal text all together.

## Expected Results:
- `inline code` → orange background, small font
- ```code blocks``` → gray background, copy button, larger font
- **bold text** → bold weight, NOT code styling
