import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection,
} from "streamlit-component-lib"
import React, { ReactNode } from "react"
import Tabs from "@mui/material/Tabs"
import Tab from "@mui/material/Tab"
import Box from "@mui/material/Box"
import { ThemeProvider, createTheme } from "@mui/material"
import { orange } from "@mui/material/colors"

const theme = createTheme({
  palette: {
    primary: orange,
  },
})

function BasicTabs({
  tabs,
  selectedTab,
}: {
  tabs: string[]
  selectedTab: number
}) {
  const [value, setValue] = React.useState(selectedTab)
  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    Streamlit.setComponentValue(tabs[newValue])
    setValue(newValue)
  }

  return (
    <Box sx={{ width: "100%", margin: -1, padding: 0 }}>
      <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Tabs
          value={value}
          onChange={handleChange}
          aria-label="navigation-tabs"
        >
          {tabs.map((tab) => (
            <Tab key={`custom-tab-${tab}`} label={tab} />
          ))}
        </Tabs>
      </Box>
    </Box>
  )
}

class StreamlitTabs extends StreamlitComponentBase<{}> {
  public render = (): ReactNode => {
    const tabs = this.props.args["tabs"]
    const selectedTab = this.props.args["selected_tab"]
    return (
      <ThemeProvider theme={theme}>
        <BasicTabs tabs={tabs} selectedTab={selectedTab} />
      </ThemeProvider>
    )
  }
}

export default withStreamlitConnection(StreamlitTabs)
