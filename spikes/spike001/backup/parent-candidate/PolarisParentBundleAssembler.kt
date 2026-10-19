package polaris.spike001.backup.parent

import eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundle

/** Staging-only bridge from the existing export planner to a v2 *full-parent* archive. */
object PolarisParentBundleAssembler {
    fun assemble(base: BackupPolarisBundle, split: PolarisParentPartition): BackupPolarisBundle {
        require(base.formatVersion == BackupPolarisBundle.CURRENT_FORMAT_VERSION && base.parentSnapshots.isEmpty()) {
            "Only an ordinary v1 planner result may be upgraded to full-parent v2"
        }
        require(base.works.isNotEmpty()) { "Do not emit an empty v2 archive" }
        require(split.ordinaryManga.none { it.source == 6969L }) { "Virtual manga leaked to ordinary lane" }
        require(split.originalCount == split.ordinaryManga.size + split.virtualParents.size) {
            "Incomplete original snapshot partition"
        }
        // Prove complete snapshots survive the split; there is no title-based matching.
        split.reassembleOriginalOrder()
        val upgraded = base.copy(
            formatVersion = BackupPolarisBundle.FULL_PARENT_FORMAT_VERSION,
            parentSnapshots = split.virtualParents,
        )
        upgraded.validateSnapshotCoverage(split.ordinaryManga)
        return upgraded
    }
}
