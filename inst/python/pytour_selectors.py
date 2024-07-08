import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from functools import partial
import time

from matplotlib.path import Path
from matplotlib.widgets import LassoSelector
from mpl_toolkits.axes_grid1 import make_axes_locatable

from helpers import gram_schmidt
# Helper class that manages the lasso selection


class LassoSelect:
    def __init__(self, plot_dicts, subplot_idx, colors, n_pts):
        # initialize arguments
        self.n_pts = n_pts
        self.plot_dicts = plot_dicts
        self.subplot_idx = subplot_idx
        self.canvas = plot_dicts[subplot_idx]["ax"].figure.canvas
        self.collection = plot_dicts[subplot_idx]["ax"].collections[0]
        self.fc = self.plot_dicts[0]["fc"]
        self.colors = colors
        self.data = plot_dicts[subplot_idx]["data"]

        # initialize lasso selector
        self.lasso = LassoSelector(
            plot_dicts[subplot_idx]["ax"],
            onselect=partial(self.onselect),
            button=1)
        self.ind = []
    # onselect governs what happens with selected data points
    # changes alpha of selected data points
    # saves indices of selected data points

    def onselect(self, verts):
        path = Path(verts)
        xys = self.collection.get_offsets()
        self.ind = np.nonzero(path.contains_points(xys))[0]

        # Check which subset is active
        for col_idx, subselection_var in enumerate(self.plot_dicts[0]["subselection_vars"]):
            # If subset is active
            if subselection_var.get() == 1:
                # change facecolors
                self.plot_dicts[0]["fc"][self.ind] = [self.colors[col_idx]]
                # Change subselections
                for idx, subselection in enumerate(self.plot_dicts[0]["subselections"]):
                    # if the looped over subset isn't the currently selected, remove
                    # newly selected indices from old subsets
                    if col_idx != idx:
                        if set(self.ind) & set(subselection):
                            updated_ind = np.setdiff1d(subselection, self.ind)
                            self.plot_dicts[0]["subselections"][idx] = updated_ind

                # get set of old selection and new selection
                selected_set = list(set(self.ind).union(
                    set(self.plot_dicts[0]["subselections"][col_idx])))
                self.plot_dicts[0]["subselections"][col_idx] = np.array(
                    selected_set)

        self.collection.set_facecolors(self.plot_dicts[0]["fc"])

        # update other plots if applicable
        for subplot_idx, plot_dict in enumerate(self.plot_dicts):
            # check plots if they are scatterplots. if so recolor datapoints
            if plot_dict["type"] == "scatter":
                collection_subplot = plot_dict["ax"].collections[0]
                collection_subplot.set_facecolors(self.plot_dicts[0]["fc"])

            elif plot_dict["type"] == "hist":
                if plot_dict["subtype"] == "1d_tour":
                    feature_selection = plot_dict["feature_selection"]
                    plot_dict["proj"][feature_selection, 0] = plot_dict["proj"][feature_selection, 0] / \
                        np.linalg.norm(
                            plot_dict["proj"][feature_selection, 0])
                    x = np.matmul(plot_dict["data"][:, feature_selection],
                                  plot_dict["proj"][feature_selection])/plot_dict["half_range"]
                    x = x[:, 0]
                else:
                    x = plot_dict["data"][:, plot_dict["hist_feature"]]

                # Get x and y_lims of old plot
                x_lims = plot_dict["ax"].get_xlim()
                y_lims = plot_dict["ax"].get_ylim()
                title = plot_dict["ax"].get_title()
                x_label = plot_dict["ax"].get_xlabel()

                x_subselections = []
                for subselection in self.plot_dicts[0]["subselections"]:
                    if subselection.shape[0] != 0:
                        x_subselections.append(x[subselection])
                    else:
                        x_subselections.append(np.array([]))

                plot_dict["ax"].clear()
                plot_dict["ax"].hist(
                    x_subselections,
                    stacked=True,
                    picker=True,
                    color=self.colors[:len(x_subselections)])

                plot_dict["ax"].set_ylim(y_lims)
                plot_dict["ax"].set_xlim(x_lims)
                plot_dict["ax"].set_title(title)
                plot_dict["ax"].set_xlabel(x_label)

            elif plot_dict["type"] == "cat_clust_interface":
                cat_clust_data = np.empty(
                    (len(plot_dict["feature_selection"]),
                     len(plot_dict["subselection_vars"])))

                n_subsets = len(plot_dict["subselection_vars"])
                data = self.plot_dicts[subplot_idx]["data"]
                # get ratios
                all_pos = np.sum(plot_dict["data"], axis=0)
                for subset_idx, subset in enumerate(plot_dict["subselections"]):
                    if subset.shape[0] != 0:
                        all_pos_subset = np.sum(
                            plot_dict["data"][subset], axis=0)
                        if plot_dict["subtype"] == "Intra cluster fraction of positive":
                            cat_clust_data[:,
                                           subset_idx] = all_pos_subset/self.data[subset].shape[0]
                        elif plot_dict["subtype"] == "Total fraction of positive":
                            cat_clust_data[:,
                                           subset_idx] = all_pos_subset/all_pos
                        elif plot_dict["subtype"] == "Total fraction":
                            cat_clust_data[:,
                                           subset_idx] = all_pos_subset/self.data.shape[0]
                    else:
                        cat_clust_data[:, subset_idx] = np.zeros(
                            len(plot_dict["feature_selection"]))
                var_ids = np.repeat(np.arange(sum(plot_dict["feature_selection"])),
                                    n_subsets)
                cat_clust_data = cat_clust_data.flatten()

                # make cluster color scheme
                clust_colors = np.tile(self.colors,
                                       (len(plot_dict["feature_selection"]), 1))
                clust_colors = np.concatenate((clust_colors,
                                               np.ones((clust_colors.shape[0], 1))),
                                              axis=1)
                clust_ids = np.arange(n_subsets)
                clust_ids = np.tile(clust_ids, len(
                    plot_dict["feature_selection"]))

                # current cluster selection
                for subselection_id, subselection_var in enumerate(plot_dict["subselection_vars"]):
                    if subselection_var.get() == 1:
                        selected_cluster = subselection_id

                not_selected = np.where(
                    clust_ids != selected_cluster)[0]
                clust_colors[not_selected, -1] = 0.2

                feature_selection_bool = np.repeat(
                    plot_dict["feature_selection"], n_subsets)

                x = cat_clust_data[feature_selection_bool]
                fc = clust_colors[feature_selection_bool]

                # Sort to display inter cluster max at the top
                sort_idx = np.arange(
                    selected_cluster, x.shape[0], n_subsets, dtype=int)
                ranked_vars = np.argsort(x[sort_idx])[::-1]
                sorting_helper = np.arange(x.shape[0])
                sorting_helper = sorting_helper.reshape(
                    sort_idx.shape[0], int(n_subsets))
                sorting_helper = sorting_helper[ranked_vars].flatten()

                # flip var_ids so most important is on top
                var_ids = np.flip(var_ids)

                self.plot_dicts[subplot_idx]["ax"].clear()
                self.plot_dicts[subplot_idx]["ax"].scatter(
                    x[sorting_helper],
                    var_ids,
                    c=fc[sorting_helper])

                y_tick_labels = np.array(plot_dict["col_names"])[
                    plot_dict["feature_selection"]]
                y_tick_labels = y_tick_labels[ranked_vars]
                # flip so that labels agree with var_ids
                y_tick_labels = np.flip(y_tick_labels)

                self.plot_dicts[subplot_idx]["ax"].set_yticks(
                    np.arange(0, sum(plot_dict["feature_selection"])))
                self.plot_dicts[subplot_idx]["ax"].set_yticklabels(
                    y_tick_labels)
                self.plot_dicts[subplot_idx]["ax"].set_xlabel(
                    plot_dict["subtype"])

                subselections = self.plot_dicts[subplot_idx]["subselections"]
                subset_size = data[subselections[selected_cluster]].shape[0]
                fraction_of_total = (subset_size/data.shape[0])*100
                title = f"{subset_size} obersvations - ({fraction_of_total:.2f}%)"
                self.plot_dicts[subplot_idx]["ax"].set_title(title)

                self.plot_dicts[subplot_idx]["cat_clust_data"] = cat_clust_data

        self.canvas.draw_idle()

    # governs what happens when disconnected (after pressing "enter")
    def disconnect(self):
        self.lasso.disconnect_events()
        self.canvas.draw_idle()


class BarSelect:
    def __init__(self, plot_dicts, subplot_idx, feature_selection, colors, half_range):
        # initialize parameters
        self.plot_dicts = plot_dicts
        self.subplot_idx = subplot_idx
        self.plot_dict = self.plot_dicts[self.subplot_idx]
        self.feature_selection = feature_selection
        self.half_range = half_range
        self.ax = plot_dicts[subplot_idx]["ax"]
        self.data = plot_dicts[subplot_idx]["data"]
        self.subtype = plot_dicts[subplot_idx]["subtype"]
        if self.subtype == "hist":
            self.hist_feature = plot_dicts[subplot_idx]["hist_feature"]

        self.canvas = self.ax.figure.canvas
        self.collection = self.ax.collections
        self.patches = self.ax.patches
        self.y_lims = self.ax.get_ylim()
        self.colors = colors

        self.connection = self.ax.figure.canvas.mpl_connect("pick_event", partial(
            self.onselect))
        self.ind = []

        # transform x if necessary and save transform. Do we need this???
        for subplot_idx, plot_dict in enumerate(self.plot_dicts):
            if not isinstance(plot_dict, int):
                if plot_dict["subtype"] == "1d_tour":
                    plot_dict["proj"][self.feature_selection, 0] = plot_dict["proj"][self.feature_selection, 0] / \
                        np.linalg.norm(
                            plot_dict["proj"][self.feature_selection, 0])
                    x = np.matmul(plot_dict["data"][:, self.feature_selection],
                                  plot_dict["proj"][self.feature_selection])/self.half_range
                    self.plot_dicts[subplot_idx]["x"] = x[:, 0]
                elif plot_dict["subtype"] == "hist":
                    self.plot_dicts[subplot_idx]["x"] = plot_dict["data"][:,
                                                                          plot_dict["hist_feature"]]

    # onselect governs what happens with selected data points
    # changes alpha of selected data points
    # saves indices of selected data points

    def onselect(self, event):
        if event.artist.axes != self.ax:
            return

        min_select = event.artist.get_x()
        max_select = min_select+event.artist.get_width()
        cur_plot_dict = self.plot_dicts[self.subplot_idx]

        if cur_plot_dict["subtype"] == "1d_tour":
            cur_plot_dict["proj"][self.feature_selection, 0] = cur_plot_dict["proj"][self.feature_selection, 0] / \
                np.linalg.norm(
                    cur_plot_dict["proj"][self.feature_selection, 0])
            x = np.matmul(cur_plot_dict["data"][:, self.feature_selection],
                          cur_plot_dict["proj"][self.feature_selection])/self.half_range
            x = x[:, 0]
            cur_plot_dict["x"] = x

        new_ind = np.where(np.logical_and(
            cur_plot_dict["x"] >= min_select,
            cur_plot_dict["x"] <= max_select))[0].tolist()

        # Check which subset is active
        for col_idx, subselection_var in enumerate(self.plot_dicts[0]["subselection_vars"]):
            # If subset is active
            if subselection_var.get() == 1:
                # add new_ind to old selection
                merged_selection = list(
                    self.plot_dicts[0]["subselections"][col_idx]) + list(new_ind)
                merged_selection = np.array(list(set(merged_selection)))
                self.plot_dicts[0]["subselections"][col_idx] = merged_selection

                # remove new selection from other selections
                for idx, subselection in enumerate(self.plot_dicts[0]["subselections"]):
                    # if the looped over subset isn't the currently selected, remove
                    # newly selected indices from old subsets
                    if col_idx != idx:
                        removed_selection = np.setdiff1d(
                            subselection, new_ind)
                        self.plot_dicts[0]["subselections"][idx] = removed_selection

        for col_idx, subselection in enumerate(self.plot_dicts[0]["subselections"]):
            if subselection.shape[0] != 0:
                self.plot_dicts[0]["fc"][subselection] = self.colors[col_idx]

        for subplot_idx, plot_dict in enumerate(self.plot_dicts):
            # update colors of scatterplot
            if plot_dict["type"] == "scatter":
                collection_subplot = plot_dict["ax"].collections[0]
                collection_subplot.set_facecolors(self.plot_dicts[0]["fc"])

            # update colors of histograms
            elif plot_dict["type"] == "hist":
                if plot_dict["subtype"] == "1d_tour":
                    feature_selection = plot_dict["feature_selection"]
                    plot_dict["proj"][feature_selection, 0] = plot_dict["proj"][feature_selection, 0] / \
                        np.linalg.norm(
                            plot_dict["proj"][feature_selection, 0])
                    x = np.matmul(plot_dict["data"][:, feature_selection],
                                  plot_dict["proj"][feature_selection])/plot_dict["half_range"]
                    x = x[:, 0]
                else:
                    x = plot_dict["data"][:, plot_dict["hist_feature"]]

                # Get x and y_lims of old plot
                x_lims = plot_dict["ax"].get_xlim()
                y_lims = plot_dict["ax"].get_ylim()
                title = plot_dict["ax"].get_title()
                x_label = plot_dict["ax"].get_xlabel()

                x_subselections = []
                for subselection in self.plot_dicts[0]["subselections"]:
                    if subselection.shape[0] != 0:
                        x_subselections.append(x[subselection])
                    else:
                        x_subselections.append(np.array([]))

                plot_dict["ax"].clear()
                plot_dict["ax"].hist(
                    x_subselections,
                    stacked=True,
                    picker=True,
                    color=self.colors[:len(x_subselections)])

                plot_dict["ax"].set_ylim(y_lims)
                plot_dict["ax"].set_xlim(x_lims)
                plot_dict["ax"].set_title(title)
                plot_dict["ax"].set_xlabel(x_label)

            elif plot_dict["type"] == "cat_clust_interface":
                cat_clust_data = np.empty(
                    (len(plot_dict["feature_selection"]),
                     len(plot_dict["subselection_vars"])))

                n_subsets = len(plot_dict["subselection_vars"])
                # get ratios
                all_pos = np.sum(plot_dict["data"], axis=0)
                for subset_idx, subset in enumerate(plot_dict["subselections"]):
                    if subset.shape[0] != 0:
                        all_pos_subset = np.sum(
                            plot_dict["data"][subset], axis=0)
                        if plot_dict["subtype"] == "Intra cluster fraction of positive":
                            cat_clust_data[:,
                                           subset_idx] = all_pos_subset/self.data[subset].shape[0]
                        elif plot_dict["subtype"] == "Total fraction of positive":
                            cat_clust_data[:,
                                           subset_idx] = all_pos_subset/all_pos
                        elif plot_dict["subtype"] == "Total fraction":
                            cat_clust_data[:,
                                           subset_idx] = all_pos_subset/self.data.shape[0]
                    else:
                        cat_clust_data[:, subset_idx] = np.zeros(
                            len(plot_dict["feature_selection"]))
                var_ids = np.repeat(np.arange(sum(plot_dict["feature_selection"])),
                                    n_subsets)
                cat_clust_data = cat_clust_data.flatten()

                # make cluster color scheme
                clust_colors = np.tile(self.colors,
                                       (len(plot_dict["feature_selection"]), 1))
                clust_colors = np.concatenate((clust_colors,
                                               np.ones((clust_colors.shape[0], 1))),
                                              axis=1)
                clust_ids = np.arange(n_subsets)
                clust_ids = np.tile(clust_ids, len(
                    plot_dict["feature_selection"]))

                # current cluster selection
                for subselection_id, subselection_var in enumerate(plot_dict["subselection_vars"]):
                    if subselection_var.get() == 1:
                        selected_cluster = subselection_id

                not_selected = np.where(
                    clust_ids != selected_cluster)[0]
                clust_colors[not_selected, -1] = 0.2

                feature_selection_bool = np.repeat(
                    plot_dict["feature_selection"], n_subsets)

                x = cat_clust_data[feature_selection_bool]
                fc = clust_colors[feature_selection_bool]

                # Sort to display inter cluster max at the top
                sort_idx = np.arange(
                    selected_cluster, x.shape[0], n_subsets, dtype=int)
                ranked_vars = np.argsort(x[sort_idx])[::-1]
                sorting_helper = np.arange(x.shape[0])
                sorting_helper = sorting_helper.reshape(
                    sort_idx.shape[0], int(n_subsets))
                sorting_helper = sorting_helper[ranked_vars].flatten()

                # flip var_ids so most important is on top
                var_ids = np.flip(var_ids)

                self.plot_dicts[subplot_idx]["ax"].clear()
                self.plot_dicts[subplot_idx]["ax"].scatter(
                    x[sorting_helper],
                    var_ids,
                    c=fc[sorting_helper])

                y_tick_labels = np.array(plot_dict["col_names"])[
                    plot_dict["feature_selection"]]
                y_tick_labels = y_tick_labels[ranked_vars]
                # flip so that labels agree with var_ids
                y_tick_labels = np.flip(y_tick_labels)

                self.plot_dicts[subplot_idx]["ax"].set_yticks(
                    np.arange(0, sum(plot_dict["feature_selection"])))
                self.plot_dicts[subplot_idx]["ax"].set_yticklabels(
                    y_tick_labels)
                self.plot_dicts[subplot_idx]["ax"].set_xlabel(
                    plot_dict["subtype"])

                subselections = self.plot_dicts[subplot_idx]["subselections"]
                subset_size = self.data[subselections[selected_cluster]].shape[0]
                fraction_of_total = (subset_size/self.data.shape[0])*100
                title = f"{subset_size} obersvations - ({fraction_of_total:.2f}%)"
                self.plot_dicts[subplot_idx]["ax"].set_title(title)

                self.plot_dicts[subplot_idx]["cat_clust_data"] = cat_clust_data

        self.canvas.draw_idle()

    def disconnect(self):
        self.canvas.mpl_disconnect(self.connection)
        self.canvas.draw_idle()


class DraggableAnnotation1d:
    def __init__(self, data, plot_dicts, subplot_idx, hist, half_range, feature_selection, colors, labels):
        self.data = data
        self.plot_dicts = plot_dicts
        self.subplot_idx = subplot_idx
        self.feature_selection = feature_selection
        self.colors = colors
        self.proj = plot_dicts[subplot_idx]["proj"]
        self.proj.setflags(write=True)
        self.press = None
        self.ax = plot_dicts[subplot_idx]["ax"]
        self.hist = hist
        self.half_range = half_range

        self.arrs = []
        self.labels = []

        if len(self.feature_selection) > 10:
            self.alpha = 0.1
        else:
            self.alpha = 1

        # Receive full projection
        self.proj[self.feature_selection, 0] = self.proj[self.feature_selection, 0] / \
            np.linalg.norm(self.proj[self.feature_selection, 0])

        divider = make_axes_locatable(self.ax)
        self.arrow_axs = divider.append_axes(
            "bottom", 1, pad=0.1)
        self.ax.tick_params(axis="x", labelbottom=False)
        self.arrow_axs.tick_params(
            axis="y", which="both", left=False, labelleft=False)
        self.arrow_axs.set_ylim(-0.05, 1.05)
        self.arrow_axs.set_xlim(-1, 1)

        true_counter = 0
        for axis_id, feature_bool in enumerate(self.feature_selection):
            if feature_bool == True:
                if len(self.feature_selection) < 10:
                    x_0 = 0
                    y_0 = axis_id/len(self.feature_selection)
                    dx = self.proj[axis_id, 0]
                    dy = 0
                else:
                    true_counter += 1
                    x_0 = 0
                    y_0 = true_counter/sum(self.feature_selection)
                    dx = self.proj[axis_id, 0]
                    dy = 0

                arr = self.arrow_axs.arrow(x_0, y_0,
                                           dx, dy,
                                           head_width=0.1,
                                           length_includes_head=True)

                label = self.arrow_axs.text(dx, y_0,
                                            labels[axis_id],
                                            alpha=self.alpha)

                self.cidpress = arr.figure.canvas.mpl_connect(
                    "button_press_event", self.on_press)
                self.cidrelease = arr.figure.canvas.mpl_connect(
                    "button_release_event", self.on_release)
                self.cidmotion = arr.figure.canvas.mpl_connect(
                    "motion_notify_event", self.on_motion)
            else:
                arr = None
                if len(self.feature_selection) < 10:
                    label = self.arrow_axs.text(0,
                                                axis_id /
                                                len(self.feature_selection),
                                                labels[axis_id],
                                                alpha=self.alpha)
                else:
                    label = None
            self.arrs.append(arr)
            self.labels.append(label)

    def on_press(self, event):
        """Check whether mouse is over us; if so, store some data."""
        # Iterate through projection axes
        for axis_id, arr in enumerate(self.arrs):
            if arr is not None:
                if event.inaxes == arr.axes and event.button == 3:
                    contains, attrd = arr.contains(event)
                    if contains:
                        self.press = axis_id

    def on_motion(self, event):
        """Move the rectangle if the mouse is over us."""
        if self.alpha != 1:
            if event.inaxes == self.arrow_axs:
                for label_idx, label in enumerate(self.labels):
                    label_pos = label.get_position()
                    if (label_pos[0] > event.xdata-0.3) and (label_pos[0] < event.xdata+0.1) and \
                            (label_pos[1] > event.ydata-0.1) and (label_pos[1] < event.ydata+0.1):
                        self.labels[label_idx].set_alpha(1)
                    else:
                        self.labels[label_idx].set_alpha(0.1)

                self.ax.figure.canvas.draw_idle()

        if self.press is None:
            return
        axis_id = self.press
        if event.xdata and event.ydata is not False:
            # Update projections
            self.proj[axis_id] = event.xdata
            # Orthonormalize
            self.proj[self.feature_selection, 0] = self.proj[self.feature_selection, 0] / \
                np.linalg.norm(self.proj[self.feature_selection, 0])

            for axis_id, feature_bool in enumerate(self.feature_selection):
                if feature_bool == True:
                    self.arrs[axis_id].set_data(dx=self.proj[axis_id, 0])
                    if self.labels[axis_id] != None:
                        # Update labels
                        self.labels[axis_id].set_x(self.proj[axis_id])

            x = np.matmul(self.data[:, self.feature_selection],
                          self.proj[self.feature_selection])/self.half_range
            x = x[:, 0]
            self.plot_dicts[self.subplot_idx]["x"] = x

            title = self.ax.get_title()
            x_label = self.ax.get_xlabel()

            # check if there are preselected points and update plot
            x_subselections = []
            for subselection in self.plot_dicts[0]["subselections"]:
                if subselection.shape[0] != 0:
                    x_subselections.append(x[subselection])
                else:
                    x_subselections.append(np.array([]))
            self.plot_dicts[self.subplot_idx]["ax"].clear()
            self.plot_dicts[self.subplot_idx]["ax"].hist(
                x_subselections,
                stacked=True,
                picker=True,
                color=self.colors[:len(x_subselections)])

            bar_selector = BarSelect(plot_dicts=self.plot_dicts,
                                     subplot_idx=self.subplot_idx,
                                     feature_selection=self.feature_selection,
                                     colors=self.colors,
                                     half_range=self.half_range)
            self.plot_dicts[self.subplot_idx]["selector"] = bar_selector

            # redraw
            self.ax.tick_params(axis="x", labelbottom=False)
            self.arrow_axs.tick_params(axis="y", which="both", labelleft=False)
            self.ax.set_title(title)
            self.ax.set_xlabel(x_label)
            self.ax.set_xlim(-1, 1)
            self.ax.figure.canvas.draw()

    def on_release(self, event):
        """Clear button press information."""
        self.press = None

    def remove(self):
        self.arrow_axs.remove()


class DraggableAnnotation2d:
    def __init__(self, data, proj, ax, scat, half_range, feature_selection, labels):
        self.data = data
        self.feature_selection = feature_selection
        self.proj = proj
        self.proj.setflags(write=True)
        self.press = None
        self.ax = ax
        self.scat = scat
        self.half_range = half_range

        if len(self.feature_selection) > 10:
            self.alpha = 0.1
        else:
            self.alpha = 1

        self.arrs = []
        self.labels = []
        # Receive full projection
        self.proj[self.feature_selection, 0] = self.proj[self.feature_selection, 0] / \
            np.linalg.norm(self.proj[self.feature_selection, 0])
        self.proj[self.feature_selection, 1] = gram_schmidt(
            self.proj[self.feature_selection, 0], self.proj[self.feature_selection, 1])
        self.proj[self.feature_selection, 1] = self.proj[self.feature_selection, 1] / \
            np.linalg.norm(self.proj[self.feature_selection, 1])

        for axis_id, feature_bool in enumerate(self.feature_selection):
            if feature_bool == True:
                arr = self.ax.arrow(0, 0,
                                    self.proj[axis_id, 0]*2/3,
                                    self.proj[axis_id, 1]*2/3,
                                    head_width=0.06,
                                    length_includes_head=True)

                label = self.ax.text(self.proj[axis_id, 0]*2/3,
                                     self.proj[axis_id, 1]*2/3,
                                     labels[axis_id],
                                     alpha=self.alpha)

                self.cidpress = arr.figure.canvas.mpl_connect(
                    "button_press_event", self.on_press)
                self.cidrelease = arr.figure.canvas.mpl_connect(
                    "button_release_event", self.on_release)
                self.cidmotion = arr.figure.canvas.mpl_connect(
                    "motion_notify_event", self.on_motion)
            else:
                arr = None
                label = None
            self.arrs.append(arr)
            self.labels.append(label)

    def on_press(self, event):
        """Check whether mouse is over us; if so, store some data."""
        # Iterate through projection axes
        for axis_id, arr in enumerate(self.arrs):
            if arr is not None:
                if event.inaxes == arr.axes and event.button == 3:
                    contains, attrd = arr.contains(event)
                    if contains:
                        self.press = axis_id

    def on_motion(self, event):
        """Move the rectangle if the mouse is over us."""

        if event.inaxes == self.ax:
            if self.alpha != 1:
                for label_idx, label in enumerate(self.labels):
                    label_pos = label.get_position()
                    if (label_pos[0] > event.xdata-0.3) and (label_pos[0] < event.xdata+0.1) and \
                            (label_pos[1] > event.ydata-0.1) and (label_pos[1] < event.ydata+0.1):
                        self.labels[label_idx].set_alpha(1)
                    else:
                        self.labels[label_idx].set_alpha(0.1)

                self.ax.figure.canvas.draw_idle()

        if self.press is None:
            return
        axis_id = self.press

        if event.xdata and event.ydata is not False:
            # Update projections
            self.proj[axis_id] = [event.xdata/(2/3), event.ydata/(2/3)]
            # Orthonormalize
            self.proj[self.feature_selection, 0] = self.proj[self.feature_selection, 0] / \
                np.linalg.norm(self.proj[self.feature_selection, 0])
            self.proj[self.feature_selection, 1] = gram_schmidt(
                self.proj[self.feature_selection, 0], self.proj[self.feature_selection, 1])
            self.proj[self.feature_selection, 1] = self.proj[self.feature_selection, 1] / \
                np.linalg.norm(self.proj[self.feature_selection, 1])

            for axis_id, feature_bool in enumerate(self.feature_selection):
                if feature_bool == True:
                    self.arrs[axis_id].set_data(x=0,
                                                y=0,
                                                dx=self.proj[axis_id,
                                                             0]*2/3,
                                                dy=self.proj[axis_id,
                                                             1]*2/3)

                    # Update labels
                    self.labels[axis_id].set_x(self.proj[axis_id, 0]*2/3)
                    self.labels[axis_id].set_y(self.proj[axis_id, 1]*2/3)

            # Update scattplot locations
            new_data = np.matmul(self.data[:, self.feature_selection],
                                 self.proj[self.feature_selection])/self.half_range
            self.scat.set_offsets(new_data)

            # redraw
            # self.ax.figure.canvas.draw()
            # self.ax.draw_artist(self.scat)
            # self.ax.figure.canvas.update()
            self.ax.figure.canvas.draw_idle()
            self.ax.figure.canvas.flush_events()

    def on_release(self, event):
        """Clear button press information."""
        self.press = None
