from ornata import application, components
from ornata.application import AppConfig
from ornata.definitions.dataclasses.components import ComponentContent

config = AppConfig(
    title="Testing Ornata",
    backend=application.BackendTarget.CLI,
    viewport_width=1280,
    viewport_height=720,
    stylesheets=[
        "src/ornata/styling/theming/assets/default.osts",
    ],
)
app = application.Application(config)
title = components.TextComponent(component_name="Title", content=ComponentContent(text="Hello World. this is a test to see how wide it will fit the text on one single line :) so if this seems like nonsense, it definitely is, but is necessary. also, word wrapping should ensure the title is NOT truncated!"))
button = components.ButtonComponent(component_name="Button", content=ComponentContent(text="Click Me"))
container = components.ContainerComponent(component_name="Box", children=[title, button])
app.mount(container)
app.run()