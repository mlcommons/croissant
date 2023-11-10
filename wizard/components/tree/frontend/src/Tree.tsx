import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection,
} from "streamlit-component-lib"
import React, { ReactNode } from "react"
import { styled, useTheme } from "@mui/material/styles"
import Box from "@mui/material/Box"
import Typography from "@mui/material/Typography"
import FileCopyIcon from "@mui/icons-material/FileCopy"
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile"
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown"
import ArrowRightIcon from "@mui/icons-material/ArrowRight"
import { SvgIconProps } from "@mui/material/SvgIcon"
import { TreeView } from "@mui/x-tree-view/TreeView"
import {
  TreeItem,
  TreeItemProps,
  treeItemClasses,
} from "@mui/x-tree-view/TreeItem"

// All code related to the MUI tree component is taken from https://mui.com/x/react-tree-view.
declare module "react" {
  interface CSSProperties {
    "--tree-view-color"?: string
    "--tree-view-bg-color"?: string
  }
}

type StyledTreeItemProps = TreeItemProps & {
  bgColor?: string
  bgColorForDarkMode?: string
  color?: string
  colorForDarkMode?: string
  labelIcon: React.ElementType<SvgIconProps>
  labelInfo?: string
  labelText: string
}

const StyledTreeItemRoot = styled(TreeItem)(({ theme }) => ({
  color: theme.palette.text.secondary,
  [`& .${treeItemClasses.content}`]: {
    color: theme.palette.text.secondary,
    borderTopRightRadius: theme.spacing(2),
    borderBottomRightRadius: theme.spacing(2),
    paddingRight: theme.spacing(1),
    fontWeight: theme.typography.fontWeightMedium,
    "&.Mui-expanded": {
      fontWeight: theme.typography.fontWeightRegular,
    },
    "&:hover": {
      backgroundColor: theme.palette.action.hover,
    },
    "&.Mui-focused, &.Mui-selected, &.Mui-selected.Mui-focused": {
      backgroundColor: `var(--tree-view-bg-color, ${theme.palette.action.selected})`,
      color: "var(--tree-view-color)",
    },
    [`& .${treeItemClasses.label}`]: {
      fontWeight: "inherit",
      color: "inherit",
    },
  },
  [`& .${treeItemClasses.group}`]: {
    marginLeft: 0,
    [`& .${treeItemClasses.content}`]: {
      paddingLeft: theme.spacing(2),
    },
  },
})) as unknown as typeof TreeItem

const StyledTreeItem = React.forwardRef(function StyledTreeItem(
  props: StyledTreeItemProps,
  ref: React.Ref<HTMLLIElement>
) {
  const theme = useTheme()
  const {
    bgColor,
    color,
    labelIcon: LabelIcon,
    labelInfo,
    labelText,
    colorForDarkMode,
    bgColorForDarkMode,
    ...other
  } = props

  const styleProps = {
    "--tree-view-color":
      theme.palette.mode !== "dark" ? color : colorForDarkMode,
    "--tree-view-bg-color":
      theme.palette.mode !== "dark" ? bgColor : bgColorForDarkMode,
  }

  return (
    <StyledTreeItemRoot
      label={
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            p: 0.5,
            pr: 0,
          }}
        >
          <Box component={LabelIcon} color="inherit" sx={{ mr: 1 }} />
          <Typography
            variant="body2"
            sx={{
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              fontWeight: "inherit",
              flexGrow: 1,
            }}
          >
            {labelText}
          </Typography>
          <Typography variant="caption" color="inherit">
            {labelInfo}
          </Typography>
        </Box>
      }
      style={styleProps}
      {...other}
      ref={ref}
    />
  )
})

type Node = {
  name: string
  type: string
  parent: string
}

type TreeNodes = { [key: string]: TreeNode }

type TreeNode = Node & {
  children: string[]
}

const TreeNodeComponent = ({
  treeNode,
  treeNodes,
}: {
  treeNode: TreeNode
  treeNodes: TreeNodes
}) => {
  const { children } = treeNode
  const childrenNodes = children
    .filter((child) => child in treeNodes)
    .map((child) => treeNodes[child])
  const labelIcon =
    treeNode.type === "FileObject" ? InsertDriveFileIcon : FileCopyIcon
  return (
    <StyledTreeItem
      onClick={() => Streamlit.setComponentValue(treeNode.name)}
      nodeId={treeNode.name}
      labelText={treeNode.name}
      labelIcon={labelIcon}
    >
      {childrenNodes.map((childNode) => (
        <TreeNodeComponent treeNode={childNode} treeNodes={treeNodes} />
      ))}
    </StyledTreeItem>
  )
}

const TreeViewWithNodes = ({ nodes }: { nodes: Node[] }) => {
  const treeNodes: TreeNodes = {}
  nodes.forEach((node) => {
    treeNodes[node.name] = { ...node, children: [] }
  })
  nodes.forEach((node) => {
    if (node.parent && node.parent in treeNodes) {
      treeNodes[node.parent].children.push(node.name)
    }
  })

  return (
    <TreeView
      aria-label="gmail"
      defaultExpanded={["3"]}
      defaultCollapseIcon={<ArrowDropDownIcon />}
      defaultExpandIcon={<ArrowRightIcon />}
      defaultEndIcon={<div style={{ width: 24 }} />}
      sx={{ height: 264, flexGrow: 1, maxWidth: 400, overflowY: "auto" }}
    >
      {Object.values(treeNodes).map((treeNode) => {
        return (
          !treeNode.parent && (
            <TreeNodeComponent treeNode={treeNode} treeNodes={treeNodes} />
          )
        )
      })}
    </TreeView>
  )
}

class Tree extends StreamlitComponentBase<{}> {
  public render = (): ReactNode => {
    const nodes = this.props.args["nodes"]
    return <TreeViewWithNodes nodes={nodes} />
  }
}

export default withStreamlitConnection(Tree)
